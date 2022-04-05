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
service_commands = [DISCONNECT_MSG, NICK_REQUEST, NICK_REQUEST_REP, ADD, REMOVE]

SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)
users = []
nickname = ''


def send():
	while True:
		text = input('Введите команду или адресата:')
		if text == 'Help':
			# Todo: показать справку
			pass
		elif text == 'Users':
			# Todo: Запросить у сервера список пользователей
			pass
		elif text == 'Disconnect':
			client.send(DISCONNECT_MSG)
			client.close()
			break
		elif text in service_commands:
			print('Вы не можете отправить такое сообщение')
		elif text in users:
			destination = text
			text = input('Введите сообщение')
			try:
				# Todo: переписать ключи словаря на порты или нет
				client.send(f'{MSG_tag}{destination};{client.getpeername()};{text}')
			except:
				pass


def receive():
	while True:
		try:
			msg = client.recv(1024).decode(FORMAT)
			# Начинается с системного сообщения
			if msg.find(f'{ADD};') == 0:
				users.append(msg[len(f'{ADD};'):])
			elif msg.find(f'{REMOVE};') == 0:
				users.remove(msg[len(f'{REMOVE};'):])
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


def welcome():
	accepted = False
	while not accepted:
		try:
			msg = client.recv(1024).decode(FORMAT)
			global nickname
			if msg == NICK_REQUEST:
				nickname = input('Введите свой псевдоним:')
				client.send(nickname.encode(FORMAT))
			elif msg == NICK_REQUEST_REP:
				print('Такой псевдоним уже существует.')
				nickname = input('Введите другой:')
				client.send(nickname.encode(FORMAT))
			elif msg == NICK_APPROVED:
				accepted = True
				print(f'Вы подключились к серверу как {nickname}')
		except:
			print('Ошибка при задании псевдонима')
			client.close()
			return -1


def start():
	if welcome() != -1:
		# Starting Threads For Listening And Writing
		receive_thread = threading.Thread(target=receive)
		receive_thread.start()

		write_thread = threading.Thread(target=send)
		write_thread.start()
	else:
		print('Все плохо')
start()