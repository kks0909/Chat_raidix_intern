#!/usr/bin/env python3

import socket
import threading
# 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

# TODO: Заголовок = адресат, адресант, текст
# HEADER = 64
FORMAT = 'UTF-8'
DISCONNECT_MSG = '<DISCONNECT>'
NICK_REQUEST = '<NICKNAME>'
NICK_REQUEST_REP = '<NICKNAME_AGAIN>'
NICK_APPROVED = '<NICK_APPROVED>'
REMOVE = '<REMOVE>'
ADD = '<ADD>'
MSG_tag = '<MSG>'
SERVICE = '<SERVICE>'
USERS = '<USERS>'
USERS_END = '<USERS_END>'


PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

connections = {}


def remove_client(nickname):
	connections.pop(nickname)
	broadcast(REMOVE, nickname)
	# f'{nickname}' отключилсяя


def broadcast(reason, caused_client_nickname):
	# Посылаем всем, кроме клиента, совершившего действие
	for nickname, client in connections.items():
		if nickname is not caused_client_nickname:
			try:
				service_send(reason, caused_client_nickname)
				# client.send(msg.encode(FORMAT))
				print('Посылка бродкаста')
			except:
				remove_client(nickname)


def send(msg, destination_client):
	#Todo: подтверждение получения
	connections.get(destination_client).send(msg.encode(FORMAT))


def service_send(reason, destination_client):
	if destination_client in connections:
		destination_client = connections.get(destination_client)
	destination_client.send(f'{SERVICE}{reason}'.encode(FORMAT))


def handle_client(nickname):
	client = connections.get(nickname)
	while True:
		try:
			# TODO: возможность передавать большой объем
			msg = client.recv(1024).decode(FORMAT)
			print(msg)
			destination_client = msg[:msg.find(';')]
			send(msg, destination_client)
		except:
			remove_client(nickname)
			print(f'[DELETE CONNECTION] {client.getpeername()} {nickname}')
			break


def welcome(conn):
	# Добиваемся от пользователя псевдонима да так, чтоб он был уникальным
	service_send(NICK_REQUEST, conn)
	print('Запрос ника')
	nickname = conn.recv(1024).decode(FORMAT)
	while connections.get(nickname) is not None:
		service_send(NICK_REQUEST_REP, conn)
		nickname = conn.recv(1024).decode(FORMAT)

	service_send(NICK_APPROVED, conn)
	connections.update({nickname: conn})

	# Посылаем уже подключенных к серверу пользователей
	service_send(USERS, conn)
	for user in connections:
		service_send(user, conn)
	service_send(USERS_END, conn)

	print(f'[NEW CONNECTION] {conn.getpeername()} connected as {nickname}')
	broadcast(ADD, nickname)

	client_thread = threading.Thread(target=handle_client, args=(nickname,))
	client_thread.start()
	print(f'[ACTIVE CONNECTIONS] {threading.active_count() - 1}\n')


# print(type(nickname))
# print(connections)


def listening():
	server.listen()
	print(f'[LISTENING] server listening {SERVER}')
	while True:
		conn, address = server.accept()

		welcome_thread = threading.Thread(target=welcome, args=(conn,))
		welcome_thread.start()


if __name__ == '__main__':
	try:
		print('[STARTING]')
		listening()
	except KeyboardInterrupt:
		print('interrupted')
		server.close()
