#!/usr/bin/env python3

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


def remove_client(nickname):
	connections.get(nickname).close()
	connections.pop(nickname)
	broadcast(REMOVE, nickname, nickname)
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
		# # Если все-таки требуется отправить что-то большое, что не влезает в стандартный лимит
		# # Считаем, сколько информации можно отправить, создаем генератор для отправки кусочков
		# bytes_send = 0
		# service_prefix = f'{SERVICE}{reason}{PART}'.encode(FORMAT)
		# max_len_info = MAX_LEN - len(service_prefix)
		# info_text = ''.join(info).encode(FORMAT)
		# info_pieces = (info_text[i: i + max_len_info] for i in range(0, len(info_text), max_len_info))
		# for info_piece in info_pieces:
		# 	bytes_send += destination_client.send(service_prefix, info_piece)
		# # Контролируем количество отправленных байт
		# if bytes_send != len(info_text) + len(service_prefix) * (len(info_text) // MAX_LEN + 1):
		# 	service_send(reason, destination_client, *info)


def handle_client(nickname):
	client = connections.get(nickname)
	print('Обслуживаем клиента')
	print(f'[ACTIVE CONNECTIONS_2] {threading.active_count() - 2}; {threading.current_thread()}\n')
	# send_connected_users(nickname)
	while True:
		try:
			# TODO: возможность передавать большой объем
			# Структура: <MSG_BIG_tag>dest_addr<SEP>sender_addr<SEP>text_part
			msg = client.recv(MAX_LEN)
			print(f'MSG: {msg}')
			# Расшифровываем только длину байт, отведенную под тег
			reason = msg[:len_header_b].decode(FORMAT)
			print(f'REason: {reason}')
			if reason in [MSG_tag, MSG_BIG_tag]:
				destination_client = msg[len_header_b: msg.find(SEP.encode(FORMAT))].decode(FORMAT)
				print(destination_client)
				send(msg, destination_client)
			elif reason == SERVICE:
				if reason == 'help':
					# Todo: блок help
					pass
				elif reason == 'users':
					# TODO: send list of users
					pass
			else:
				raise Exception
		except:
			print(f'Сервер получил что-то странное от пользователя {nickname}: {msg.decode(FORMAT)}')
			print(f'[DELETE CONNECTION] {client.getpeername()} {nickname}')
			remove_client(nickname)
			break
	client.close()


def send_connected_users(nickname):
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
		if header not in headers:
			raise Exception
		else:
			return msg[len_header:]


	nickname = None
	try:
		# Добиваемся от пользователя псевдонима да так, чтоб он был уникальным
		service_send(NICK_REQUEST, conn)
		print(f'Запрос ника у {conn.getpeername()}')
		# TODO: MAX_LEN или не на ник?
		nickname = receive()
		while connections.get(nickname) is not None and nickname is not NICK_ERROR:
			service_send(NICK_REQUEST_REP, conn)
			nickname = receive()
		# Подтверждаем присвоение ника
		service_send(NICK_APPROVED, conn)
		# Оповещаем всех о новом подключении
		print(f'[NEW CONNECTION] {conn.getpeername()} connected as {nickname}')
		broadcast(ADD, nickname, nickname)

		# Посылаем уже подключенных к серверу пользователей
		send_connected_users(conn)

		connections.update({nickname: conn})
		print(f'Подключенные пользователи: {", ".join(connections)}')

		handle_client(nickname)
		# client_thread = threading.Thread(target=handle_client, args=(nickname,), name=nickname)
		# client_thread.start()
		# print(f'[ACTIVE CONNECTIONS] {threading.active_count() - 2}; {threading.current_thread()}\n')
	except:
		print(f'Ошибка во время подключения {conn.getpeername()}')
		print(f'[DELETE CONNECTION] {conn.getpeername()} {nickname}')
		if connections.get(nickname) is not None:
			remove_client(nickname)
		else:
			conn.close()
			return


# print(type(nickname))
# print(connections)


def listening():
	server.listen()
	print(f'[LISTENING] server listening {SERVER}')
	while True:
		conn, address = server.accept()

		welcome_thread = threading.Thread(target=welcome, args=(conn,))
		welcome_thread.start()

#
# print('[STARTING]')
# listening()

if __name__ == '__main__':
	try:
		print('[STARTING]')
		listening()
	except KeyboardInterrupt:
		print('interrupted')
		server.close()
		sys.exit()
