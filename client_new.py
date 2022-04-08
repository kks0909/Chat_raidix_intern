#!/usr/bin/env python3
import os
import signal
import socket
import sys
import threading
from math import floor

from help import *

SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)
users = []
nickname = ''


def send():
	while True:
		text = input('Введите команду или адресата:\n')
		if text == 'Help':
			# Todo: показать справку
			pass
		elif text == 'Users':
			client.send(f'{SERVICE}{USERS}'.encode(FORMAT))
		elif text in tags:
			print('Вы не можете отправить такое сообщение')
		elif text in users:
			destination = text
			text_en = input('Введите сообщение\n').encode(FORMAT)
			service_prefix = f'{MSG}{destination}{SEP}{nickname}{SEP}{len(text_en)}{SEP}'.encode(FORMAT)
			if len(text_en) < MAX_LEN - len(service_prefix):
				if client.send(service_prefix + text_en) == len(service_prefix) + len(text_en):
					print('Сообщение отправлено')
				else:
					print('Ошибка при отправке сообщения')
			else:
				send_smth_big(f'{MSG_BIG}{destination}{SEP}{nickname}{SEP}{len(text_en)}{SEP}', text_en)
		else:
			print('Такого пользователя или команды не существует.')


def send_smth_big(service_prefix, text_en):
	"""
	Если требуется отправить что-то большое, что не влезает в стандартный лимит.
	Считаем, сколько информации можно отправить, создаем генератор для отправки кусочков
	"""
	print('Отправляем что-то большое')
	bytes_send = 0
	service_prefix = service_prefix.encode(FORMAT)
	max_len_info = MAX_LEN - len(service_prefix) - 10
	# Добавляем в конец сигнал об окончании передачи большого сообщения
	text_en += MSG_BIG_END_flag.encode(FORMAT)
	text_pieces = (text_en[i: i + max_len_info] for i in range(0, len(text_en), max_len_info))
	for text_piece in text_pieces:
		bytes_send += client.send(service_prefix + text_piece)

	# Контролируем количество отправленных байт
	if bytes_send != len(text_en) + len(service_prefix) * (len(text_en) // MAX_LEN + 1):
		print('Ошибка при отправке.\nПовторная отправка.')
		send_smth_big(service_prefix, text_en)


def receive():
	"""
	Основная часть приема сообщений
	"""
	while True:
		try:
			msg = client.recv(MAX_LEN)
			# Расшифровываем только длину байт, отведенную под тег
			header = msg[:len_header_b].decode(FORMAT)
			# Начинается с системного сообщения
			if header == SERVICE:
				# Смотрим, что следует за SERVICE
				tag = msg[len_header_b: len_header_b + len_tag_b].decode(FORMAT)
				if tag == ADD:
					new_user = msg[len_header_b + len_tag_b:].decode(FORMAT)
					users.append(new_user)
					print(f'Подключился новый клиент: {new_user}')
				elif tag == REMOVE:
					rem_user = msg[len_header_b + len_tag_b:].decode(FORMAT)
					users.remove(rem_user)
					print(f'Клиент отключился: {rem_user}')
				elif tag == USERS:
					get_users(msg.decode(FORMAT))
				elif tag == DISCONNECT:
					print('Вы были отключены')
					shutdown()
				elif tag == MSG_CONTROL:
					# TODO: потеря сообщения не обрабатывается
					msg = msg.decode(FORMAT)
					flag, len_text_b = msg[len_header + len_tag:].split(SEP)[1:]
					if flag == MSG_Y:
						print('Ваше сообщение доставлено')
					elif flag == MSG_N:
						print('Ваше сообщение частично не доставлено')
				else:
					print(f'Получено сообщение с пометкой системное, не удалось обработать:\n{msg}')
			# Имеет хедер сообщения
			elif header == MSG:
				# Структура сообщения: <MSG>dest_nick<SEP>sender_nick<SEP>len_text_b<SEP>text
				msg = msg.decode(FORMAT)
				destination, sender, len_text_b, text = msg[len_header:].split(SEP, 3)
				if len(text.encode(FORMAT)) == int(len_text_b):
					print(f'Получено сообщение от {sender}:\n{text}')
					client.send(f'{SERVICE}{MSG_CONTROL}{sender}{SEP}{MSG_Y}{SEP}{len_text_b}'.encode(FORMAT))
				else:
					print(f'Получено битое сообщение от {sender}. Попытка расшифровать:\n{text}')
					client.send(f'{SERVICE}{MSG_CONTROL}{sender}{SEP}{MSG_N}{SEP}{len_text_b}'.encode(FORMAT))
			elif header == MSG_BIG:
				# Структура сообщения: <MSG_BIG_tag>dest_nick<SEP>sender_nick<SEP>text_part
				destination, sender, len_text_b, text_en = msg[len_header_b:].split(SEP.encode(FORMAT), 3)
				destination, sender, len_text_b = [item.decode(FORMAT) for item in [destination, sender, len_text_b]]
				while True:
					msg = client.recv(MAX_LEN)
					new_destination, new_sender, new_len_text_b, new_text_en = msg[len_header_b:].split(SEP.encode(FORMAT), 3)
					new_destination, new_sender, new_len_text_b = [item.decode(FORMAT) for item in [new_destination, new_sender, new_len_text_b]]
					if new_destination == destination and new_sender == sender and new_len_text_b == len_text_b:
						if not new_text_en.endswith(MSG_BIG_END_flag.encode(FORMAT)):
							text_en += new_text_en
						else:
							text_en += new_text_en[:-len(MSG_BIG_END_flag)]
							if len(text_en) == int(len_text_b):
								print(f'Получено большое сообщение от {sender}:\n{text_en.decode(FORMAT)}')
								client.send(f'{SERVICE}{MSG_CONTROL}{sender}{SEP}{MSG_Y}{SEP}{len_text_b}'.encode(FORMAT))
							else:
								print(f'Получено битое сообщение от {sender}.\n {len(text_en)}{len_text_b}')
								client.send(f'{SERVICE}{MSG_CONTROL}{sender}{SEP}{MSG_N}{SEP}{len_text_b}'.encode(FORMAT))
							break
					else:
						print(f'Не получено большое сообщение от {sender}.')
						client.send(f'{SERVICE}{MSG_CONTROL}{sender}{SEP}{MSG_N}{SEP}{len_text_b}'.encode(FORMAT))
						break
			else:
				print(f'Получено что-то странное: {msg}')
				raise Exception
			show_info_text()
		except:
			print('Ошибка при получении')
			shutdown()


def get_users(msg):
	print(f'Получаем список пользователей...')
	users_raw = msg[len_header + len_tag:]
	users_raw = users_raw.split(SEP)
	global users
	for user_raw in users_raw:
		if user_raw not in users and user_raw != '':
			users.append(user_raw)
	if len(users) == 0:
		print('Вы единственное подключение')
	else:
		print(f'Подключенные клиенты: {", ".join(users)}')


def service_send(tag, *msg):
	"""
	Заведомо меньше лимита
	"""
	client.send(f'{SERVICE}{tag}{"".join(msg)}'.encode(FORMAT))


def show_info_text():
	print('Введите команду или адресата:\n')


def welcome():
	"""
	Вызывается только при подключении.
	Завершается при задании псевдонима и получения списка уже подключенных пользователей.
	"""
	accepted = False
	global nickname
	
	while not accepted:
		try:
			msg = client.recv(MAX_LEN).decode(FORMAT)
			header = msg[:len_header]
			if header == SERVICE:
				# Смотрим, что следует за SERVICE
				reason = msg[len_header: len_header + len_tag]
				if reason == NICK_REQUEST:
					nickname = input(f'Введите свой псевдоним (не больше {floor(max_nickname_b / len("A".encode(FORMAT)))} символов): ')
					nickname_b = len(nickname.encode(FORMAT))
					if nickname_b <= max_nickname_b:
						service_send(NICK, nickname)
						# client.send(nickname_b)
					else:
						service_send(NICK_ERROR)
						# client.send(NICK_ERROR)
				elif reason == NICK_REQUEST_REP:
					print('Либо такой псевдоним уже существует, либо Вы превысили лимит\n')
					nickname = input('Введите другой: ')
					service_send(NICK, nickname)
					# client.send(nickname.encode(FORMAT))
				elif reason == NICK_APPROVED:
					print(f'Вы подключились к серверу как {nickname}')
				elif reason == USERS:
					get_users(msg)
					accepted = True
					return
			# 	else:
			# 		print(f'Ну чет странное: {msg}\n')
			# else:
			# 	print(f'Ну чет очень странное: {msg}\n')
		except:
			print('Ошибка при задании псевдонима')
			shutdown()
	return


def shutdown():
	client.close()
	print('Завершение работы')
	os.kill(os.getpid(), signal.SIGINT)
	sys.exit()


def start():
	try:
		welcome_thread = threading.Thread(target=welcome)
		welcome_thread.start()
		welcome_thread.join()

		receive_thread = threading.Thread(target=receive)
		receive_thread.start()

		write_thread = threading.Thread(target=send)
		write_thread.start()
	except:
		print('Все плохо')
		shutdown()


if __name__ == '__main__':
	try:
		print('[STARTING]')
		start()
	except KeyboardInterrupt:
		shutdown()
