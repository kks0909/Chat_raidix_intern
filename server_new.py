#!/usr/bin/env python3

import socket
import threading


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


PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

connections = {}


def remove_client(nickname):
	connections.pop(nickname)
	broadcast(f'{REMOVE};{nickname}', nickname)
	# f'{nickname}' отключилсяя


def broadcast(msg, caused_client_nickname):
	# Посылаем всем, кроме клиента, совершившего действие
	for nickname, client in connections.items():
		if nickname is not caused_client_nickname:
			try:
				client.send(msg)
			except:
				remove_client(nickname)


def send(msg, destination_client):
	#Todo: подтверждение получения
	connections.get(destination_client).send(msg)


def handle_client(nickname):
	# print(type(nickname))
	client = connections.get(nickname)
	print(f'[NEW CONNECTION] {client.getpeername()} connected as {nickname}')
	broadcast(f'{ADD};{nickname}', nickname)

	while True:
		try:
			# TODO: возможность передавать большой объем
			msg = client.recv(1024).decode(FORMAT)
			destination_client = msg[:msg.find(';')]
			send(msg, destination_client)
		except:
			remove_client(nickname)
			break


def welcome(conn):
	# Добиваемся от пользователя псевдонима да так, чтоб он был уникальным
	conn.send(NICK_REQUEST.encode(FORMAT))
	nickname = conn.recv(1024).decode(FORMAT)
	while connections.get(nickname) is not None:
		conn.send(NICK_REQUEST_REP.encode(FORMAT))
		nickname = conn.recv(1024).decode(FORMAT)

	conn.send(NICK_APPROVED.encode(FORMAT))
	connections.update({nickname: conn})

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


print('[STARTING]')
listening()
