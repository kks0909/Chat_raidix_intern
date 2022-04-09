#!/usr/bin/env python3
import os
import signal
import socket
import sys
import threading

from help import *

# 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


SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

connections = {}
connections_temp = []


def remove_client(nickname):
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

	# f'{nickname}' отключилсяя


def broadcast(reason, caused_client_nickname, text):
	# Посылаем всем, кроме клиента, совершившего действие
	for nickname in connections:
		if nickname is not caused_client_nickname:
			try:
				service_send(reason, nickname, text)
				print('Посылка бродкаста')
			except:
				remove_client(nickname)


def send(nickname, raw_msg):
	#Todo: подтверждение получения

	# if type(msg) is not bytes:
	# 	msg = msg.encode(FORMAT)
	connections.get(nickname).send(raw_msg)


def service_send(reason, destination_client, *info):
	print('СЕРВИС')
	if destination_client in connections:
		destination_client = connections.get(destination_client)
	elif type(destination_client) is not socket.socket:
		print('Куда, блять, отправлять?')

	# Отправляемое сообщение
	msg = MSG().set(SERVICE, tag=reason, nick="".join(info))
	# msg = f'{SERVICE}{reason}{"".join(info)}'.encode(FORMAT)
	if destination_client.send(msg) != len(msg):
		# Если произошла ошибка при отправке или отправилось не все, то повторить отправку
		service_send(reason, destination_client, *info)


def handle_client(nickname):
	client = connections.get(nickname)
	print('Обслуживаем клиента')
	print(f'[ACTIVE CONNECTIONS] {threading.active_count() - 1}; {threading.current_thread()}\n')
	# send_connected_users(nickname)
	while True:
		try:
			raw_msg = client.recv(MAX_LEN)
			msg = MSG().get(raw_msg)
			if msg.header in [MSG_NORMAL, MSG_BIG]:
				print(msg.destination)
				send(msg.destination, raw_msg)
			elif msg.header == SERVICE:
				if msg.tag == 'help':
					# Todo: блок help
					pass
				elif msg.tag == USERS:
					send_connected_users(nickname)
				elif msg.tag == MSG_CONTROL:
					print(msg.destination)
					send(msg.destination, raw_msg)
				else:
					raise Exception
			else:
				raise Exception
		except:
			print(f'Ошибка при обслуживании пользователя {nickname}.')
			remove_client(nickname)
			break
	client.close()


def send_connected_users(nickname):
	print('Подключенные юзеры')
	service_send(USERS, nickname, f'{SEP}'.join(connections))


def welcome(conn):
	def receive_nick():
		msg = MSG().get(conn.recv(MAX_LEN))
		if msg.header == SERVICE:
			if msg.tag == NICK and all([nickname, connections.get(nickname)]) is not None:
				print(msg.data)
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
		print(f'Запрос ника у {conn.getpeername()}')
		nickname = receive_nick()
		# Подтверждаем присвоение ника
		service_send(NICK_APPROVED, conn)
		# Оповещаем всех о новом подключении
		print(f'[NEW CONNECTION] {conn.getpeername()} connected as {nickname}')
		broadcast(ADD, nickname, nickname)

		# Посылаем уже подключенных к серверу пользователей
		send_connected_users(conn)

		connections.update({nickname: conn})
		print(f'Подключенные пользователи: {", ".join(connections)}')
		connections_temp.remove(conn)

		handle_client(nickname)
	except:
		print(f'Ошибка во время подключения {conn.getpeername()}')
		print(f'[DELETE CONNECTION] {conn.getpeername()} {nickname}')
		if connections.get(nickname) is not None:
			remove_client(nickname)
		else:
			remove_client(conn)


def listening():
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
		print('Interrupted')
		for client in list(connections.keys()) + connections_temp:
			remove_client(client)
		server.close()
		os.kill(os.getpid(), signal.SIGINT)
		sys.exit()


