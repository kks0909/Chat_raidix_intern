#!/usr/bin/env python3

import socket
import threading


# HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
# Todo: disconnect message
DISCONNECT_MSG = '<DISCONNECT>'
NICK_REQUEST = '<NICKNAME>'
NICK_REQUEST_REP = '<NICKNAME_AGAIN>'
NICK_APPROVED = '<NICK_APPROVED>'
REMOVE = '<REM>'
ADD = '<ADD>'
MSG_tag = '<MSG>'
SERVICE = '<SERVICE>'
USERS = '<USERS>'
USERS_END = '<USERS_END>'
len_service = len(f'{SERVICE}')
service_commands = [DISCONNECT_MSG, NICK_REQUEST, NICK_REQUEST_REP, ADD, REMOVE]

SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)
users = []
nickname = ''


def send():
	while True:
		text = input('Введите команду или адресата.\n')
		if text == 'Help':
			# Todo: показать справку
			pass
		elif text == 'Users':
			# Todo: Запросить у сервера список пользователей
			pass
		elif text == 'Disconnect':
			# Todo: обработать disconnect на сервере
			client.send(DISCONNECT_MSG)
			client.close()
			break
		elif text in service_commands:
			print('Вы не можете отправить такое сообщение')
		elif text in users:
			destination = text
			text = input('Введите сообщение\n')
			try:
				# Todo: переписать ключи словаря на порты или нет
				client.send(f'{MSG_tag}{destination};{client.getpeername()};{text}')
			except:
				pass
		else:
			print('Такого пользователя или команды не существует.')


def receive():
	"""
	Основная часть приема сообщений
	"""
	while True:
		try:
			msg = client.recv(1024).decode(FORMAT)
			print(f'Сообзеньице: {msg}\n')
			# Начинается с системного сообщения
			if msg.find(f'{SERVICE}') == 0:
				# Смотрим, что следует за SERVICE
				if msg.find(f'{ADD}') == len_service:
					new_user = msg[len(f'{ADD}'):]
					users.append(new_user)
					print(f'Клиент подключился: {new_user}')
				elif msg.find(f'{REMOVE};') == len_service:
					rem_user = msg[len(f'{REMOVE}'):]
					users.remove(rem_user)
					print(f'Клиент отключился: {rem_user}')
				elif msg.find(f'{USERS}') == len_service:
					get_connected_users()
				else:
					print(f'Получено сообщение с пометкой системное, не удалось обработать:\n{msg}')
			# Начинается с тега сообщения
			elif msg.find(f'{MSG_tag};') == 0:
				_, sender, text = msg.split(';', 2)
				print(f'Получено сообщение от {sender}:\n{text}')
				# TODO: а теперь вернуть подтверждение отправителю
			else:
				print(f'Получено что-то странное: {msg}')
		except:
			print('Ошибка при получении')
			client.close()
			break


def get_connected_users():
	"""
	Получение уже подкюченных пользователей.
	Структура сообщений:
	<SERVICE><USERS> - уже получили
	<SERVICE>username
	...
	<SERVICE><USERS_END>
	"""
	global users
	while True:
		msg = client.recv(1024).decode(FORMAT)[len_service:]
		if msg != USERS_END:
			users.append(msg)
		else:
			break
	print(f'Подключенные клиенты: {", ".join(users)}')


def welcome():
	"""
	Вызывается только при подключении
	"""
	accepted = False
	global nickname
	
	while not accepted:
		try:
			msg = client.recv(1024).decode(FORMAT)
			if msg.find(f'{SERVICE}') == 0:
				# Смотрим, что следует за SERVICE
				reason = msg[len_service:]
				if reason == NICK_REQUEST:
					nickname = input('Введите свой псевдоним: ')
					client.send(nickname.encode(FORMAT))
				elif reason == NICK_REQUEST_REP:
					print('Такой псевдоним уже существует.\n')
					nickname = input('Введите другой: ')
					client.send(nickname.encode(FORMAT))
				elif reason == NICK_APPROVED:
					print(f'Вы подключились к серверу как {nickname}')
				elif msg.find(f'{USERS}') == len_service:
					get_connected_users()
				else:
					print(f'Ну чет странное: {msg}\n')
			else:
				print(f'Ну чет очень странное: {msg}\n')
		except:
			print('Ошибка при задании псевдонима')
			client.close()
			return -1
	return 1


def start():
	if welcome() != -1:
		print('Начинаем слушать/отправлять')
		# Starting Threads For Listening And Writing
		receive_thread = threading.Thread(target=receive)
		receive_thread.start()

		write_thread = threading.Thread(target=send)
		write_thread.start()
	else:
		print('Все плохо')


start()
