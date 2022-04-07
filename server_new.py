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


def broadcast(reason, caused_client_nickname, *info):
	# Посылаем всем, кроме клиента, совершившего действие
	for nickname, client in connections.items():
		if nickname is not caused_client_nickname:
			try:
				service_send(reason, nickname, *info)
				print('Посылка бродкаста')
			except:
				remove_client(nickname)


def send(msg, destination_client):
	#Todo: подтверждение получения
	if type(msg) is not bytes:
		msg = msg.encode(FORMAT)
	connections.get(destination_client).send(msg)


def service_send(reason, destination_client, *info):
	print('СЕРВИС')
	if destination_client in connections:
		destination_client = connections.get(destination_client)
	elif type(destination_client) is not socket.socket:
		print('Куда, блять, отправлять?')

	# Отправляемое сообщение
	msg = f'{SERVICE}{reason}{"".join(info)}'.encode(FORMAT)
	if len(msg) < MAX_LEN:
		# В большинстве случаев для сервисных сообщений хватит стандартного ограничения длины
		if destination_client.sendall(msg) is not None:
			# Если произошла ошибка при отправке или отправилось не все, то повторить отправку
			service_send(reason, destination_client, *info)
	else:
		print('Отправка большого')
		if destination_client.sendall(msg) is not None:
			# Если произошла ошибка при отправке или отправилось не все, то повторить отправку
			service_send(reason, destination_client, *info)


def handle_client(nickname):
	client = connections.get(nickname)
	print('Обслуживаем клиента')
	print(f'[ACTIVE CONNECTIONS_2] {threading.active_count() - 2}; {threading.current_thread()}\n')
	# send_connected_users(nickname)
	while True:
		try:
			# Структура: <MSG_BIG_tag>dest_addr<SEP>sender_addr<SEP>text_part
			msg = client.recv(MAX_LEN)
			print(f'MSG: {msg}')
			# Расшифровываем только длину байт, отведенную под тег
			header = msg[:len_header_b].decode(FORMAT)
			print(f'REason: {header}')
			if header in [MSG_tag, MSG_BIG_tag, MSG_CONTROL]:
				destination_client = msg[len_header_b: msg.find(SEP.encode(FORMAT))].decode(FORMAT)
				print(destination_client)
				send(msg, destination_client)
			elif header == SERVICE:
				tag = msg[len_header_b: len_header_b + len_tag_b].decode(FORMAT)
				if tag == 'help':
					# Todo: блок help
					pass
				elif tag == USERS:
					send_connected_users(nickname)
				else:
					raise Exception
			else:
				raise Exception
		except:
			print(f'Сервер получил что-то странное от пользователя {nickname}: {msg.decode(FORMAT)}')
			remove_client(nickname)
			break
	client.close()


def send_connected_users(nickname):
	print('по')
	service_send(USERS, nickname, f'{SEP}'.join(connections))


def receive_msg(client):
	try:
		msg = client.recv(MAX_LEN)
		header = msg[: len_header_b].decode(FORMAT)
		if header in headers:
			return header, msg[len_header_b:],
		else:
			print(f'Ошибка во время получения')
			client.close()
	except:
		print(f'Ошибка во время получения')
		client.close()


def welcome(conn):
	def receive():
		msg = conn.recv(MAX_LEN).decode(FORMAT)
		print(msg)
		header = msg[:len_header]
		if header != SERVICE:
			raise Exception
		else:
			tag = msg[len_header: len_header + len_tag]
			if tag in [NICK, NICK_ERROR]:
				return tag, msg[len_header + len_tag:]
			raise Exception

	nickname = None
	try:
		# Добиваемся от пользователя псевдонима да так, чтоб он был уникальным
		service_send(NICK_REQUEST, conn)
		print(f'Запрос ника у {conn.getpeername()}')
		tag, nickname = receive()
		while connections.get(nickname) is not None:
			service_send(NICK_REQUEST_REP, conn)
			tag, nickname = receive()

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


