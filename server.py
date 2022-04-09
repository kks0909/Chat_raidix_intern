#!/usr/bin/env python3.9
import os
import signal
import socket
import sys
import syslog
import threading

from help import *


SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

connections = {}
connections_temp = []


def remove_client(nickname):
	"""
	Оповещение подключенных клиентов об отключении клиента (посылка сообщения с тегом DISCONNECT).
	Удаление клиента.
	"""
	if nickname in connections:
		print(f'[DELETE CONNECTION] {connections.get(nickname).getpeername()} {nickname}')
		try:
			service_send(DISCONNECT, nickname)
		finally:
			connections.get(nickname).close()
			connections.pop(nickname)
			broadcast(REMOVE, nickname, nickname)
	elif type(nickname) is socket.socket:
		print(f'[DELETE CONNECTION] {nickname}')
		try:
			service_send(DISCONNECT, nickname)
		finally:
			nickname.close()
			connections_temp.remove(nickname)


def broadcast(reason, caused_client_nickname, text):
	"""
	Оповещение всех подключенных клиентов, за исключением клиента, совершившего действие.
	Событие: отключение, добавление.
	"""
	for nickname in connections:
		if nickname is not caused_client_nickname:
			try:
				service_send(reason, nickname, text)
				print(f'[BROADCAST] {reason} {nickname}')
			except:
				remove_client(nickname)


def service_send(reason, destination_client, *info):
	"""
	Отправка сообщений с пометкой сервисных.
	Используются для всего, что не является сообщением от одного пользователя другому.
	Например: подключение/удаление пользователя, отправка списка пользователей, подтверждение получения/не получения.
	"""
	print('[SERVICE SEND]')
	if destination_client in connections:
		destination_client = connections.get(destination_client)
	elif type(destination_client) is not socket.socket:
		print('[ERROR] Ошибка при задании назначения сервисного сообщения.')

	# Отправляемое сообщение
	msg = MSG().set(SERVICE, tag=reason, nick="".join(info))
	if destination_client.send(msg) != len(msg):
		# Если произошла ошибка при отправке или отправилось не все, то повторить отправку
		service_send(reason, destination_client, *info)


def handle_client(nickname):
	"""
	Основной цикл обслуживания пользователя.
	"""
	def send(nickname, raw_msg):
		connections.get(nickname).send(raw_msg)

	client = connections.get(nickname)
	print(f'[ACTIVE CONNECTIONS] {threading.active_count() - 1}; {threading.current_thread()}\n')
	while True:
		try:
			raw_msg = client.recv(MAX_LEN)
			msg = MSG().get(raw_msg)
			if msg.header in [MSG_NORMAL, MSG_BIG]:
				# Вычленяется адрес назначения, отправляется по назначению
				syslog.syslog(syslog.LOG_INFO, msg.text_en)
				send(msg.destination, raw_msg)
			elif msg.header == SERVICE:
				if msg.tag == USERS:
					# Ответ на запрос списка подключенных пользователей
					send_connected_users(nickname)
				elif msg.tag == MSG_CONTROL:
					# Подтверждение получения письма
					send(msg.destination, raw_msg)
				else:
					raise Exception
			else:
				raise Exception
		except:
			print(f'[ERROR] Ошибка при обслуживании пользователя {nickname}.')
			remove_client(nickname)
			break
	client.close()


def send_connected_users(nickname):
	print('[SERVICE] Отправка подключенных пользователей.')
	service_send(USERS, nickname, f'{SEP}'.join(connections))


def welcome(conn):
	"""
	Запрос псевдонима у пользователя.
	При успехе псевдоним добавляется в список подключений.
	Ново-подключенный пользователь оповещается об уже подключенных пользователях.
	Остальные подключенные пользователи оповещаются о новом подключении.
	"""
	def receive_nick():
		msg = MSG().get(conn.recv(MAX_LEN))
		if msg.header == SERVICE:
			if msg.tag == NICK and all([nickname, connections.get(nickname)]) is not None:
				return msg.data
			elif msg.tag == NICK_ERROR:
				service_send(NICK_REQUEST_REP, conn)
				return receive_nick()
		else:
			raise Exception

	nickname = None
	try:
		# Добиваемся от пользователя псевдонима да так, чтоб он был уникальным
		service_send(NICK_REQUEST, conn)
		print(f'[SERVICE] Запрос ника у {conn.getpeername()}')
		nickname = receive_nick()
		# Подтверждаем присвоение ника
		service_send(NICK_APPROVED, conn)
		# Оповещаем всех о новом подключении
		print(f'[NEW CONNECTION] {conn.getpeername()} connected as {nickname}')
		print(f'[SERVICE] Подключенные пользователи: {", ".join(connections)}')
		broadcast(ADD, nickname, nickname)

		# Посылаем уже подключенных к серверу пользователей
		send_connected_users(conn)

		connections.update({nickname: conn})
		connections_temp.remove(conn)

		handle_client(nickname)
	except:
		print(f'[SERVICE] Ошибка во время подключения {conn.getpeername()}')
		print(f'[DELETE CONNECTION] {conn.getpeername()} {nickname}')
		if connections.get(nickname) is not None:
			remove_client(nickname)
		else:
			remove_client(conn)


def listening():
	"""
	Сервер постоянно слушает и принимает подключения, запуская отдельный поток.
	"""
	server.listen()
	print(f'[LISTENING] server listening {SERVER}')
	while True:
		conn, address = server.accept()
		connections_temp.append(conn)

		client_thread = threading.Thread(target=welcome, args=(conn,))
		client_thread.start()


if __name__ == '__main__':
	try:
		print('[STARTING]')
		listening()
	except KeyboardInterrupt:
		print('[INTERRUPTED]')
		for client in list(connections.keys()) + connections_temp:
			remove_client(client)
		server.close()
		os.kill(os.getpid(), signal.SIGINT)
		sys.exit()
