#!/usr/bin/env python3

import socket
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
		text = input('Введите команду или адресата.\n')
		if text == 'Help':
			# Todo: показать справку
			pass
		elif text == 'Users':
			# Todo: Запросить у сервера список пользователей
			pass
		elif text in service_commands:
			print('Вы не можете отправить такое сообщение')
		elif text in users:
			destination = text
			text_en = input('Введите сообщение\n').encode(FORMAT)
			service_prefix = f'{MSG_tag}{destination}{SEP}{nickname}{SEP}'.encode(FORMAT)
			try:
				if len(text_en) < MAX_LEN - len(service_prefix):
					print('Отправляем что-то небольшое')
					client.send(service_prefix + text_en)
				else:
					send_smth_big(f'{MSG_BIG_tag}{destination}{SEP}{nickname}{SEP}', text_en)
			except:
				# Todo: исправить
				print('За такое убивают.')
				pass
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
		print('Повторная отправка.')
		send_smth_big(service_prefix, text_en)


def receive():
	"""
	Основная часть приема сообщений
	"""
	while True:
		try:
			msg = client.recv(MAX_LEN)
			print(f'Сообзеньице: {msg}\n')
			# Расшифровываем только длину байт, отведенную под тег
			header = msg[:len_header_b].decode(FORMAT)
			print(header)
			# Начинается с системного сообщения
			if header == SERVICE:
				# Смотрим, что следует за SERVICE
				reason = msg[len_header_b: len_header_b + len_command_b].decode(FORMAT)
				print('Reason'+reason)
				if reason == ADD:
					new_user = msg[len_header_b + len_command_b:].decode(FORMAT)
					users.append(new_user)
					print(f'Новый клиент подключился: {new_user}')
				elif reason == REMOVE:
					rem_user = msg[len_header_b + len_command_b:].decode(FORMAT)
					users.remove(rem_user)
					print(f'Клиент отключился: {rem_user}')
				elif reason == USERS:
					get_users(msg)
				else:
					print(f'Получено сообщение с пометкой системное, не удалось обработать:\n{msg}')
			# Начинается с тега сообщения
			elif header == MSG_tag:
				# Структура сообщения: <MSG>dest_addr<SEP>sender_addr<SEP>text
				msg = msg.decode(FORMAT)
				destination, sender, text = msg[len(f'{MSG_tag}'):].split(SEP, 2)
				print(f'Получено сообщение от {sender}:\n{text}')
				# TODO: а теперь вернуть подтверждение отправителю
			elif header == MSG_BIG_tag:
				# Структура сообщения: <MSG_BIG_tag>dest_addr<SEP>sender_addr<SEP>text_part
				destination, sender, text = msg[len_header_b:].split(SEP.encode(FORMAT), 2)
				# destination, sender = destination.decode(FORMAT), sender.decode(FORMAT)
				while True:
					msg = client.recv(MAX_LEN)
					print(f'Новое длинное сообщеньице: {msg}')
					new_destination, new_sender, new_text = msg[len_header_b:].split(SEP.encode(FORMAT), 2)
					if new_destination == destination and new_sender == sender:
						print(len(text))
						if not new_text.endswith(MSG_BIG_END_flag.encode(FORMAT)):
							text += new_text
							print('q')
						else:
							text += new_text[:-len(MSG_BIG_END_flag)]
							print('w')
							print(f'Получено большое сообщение от {sender.decode(FORMAT)}:\n{text.decode(FORMAT)}')
							break
					else:
						print(f'Не получено большое сообщение от {sender.decode(FORMAT)}.')
						break

				# TODO: а теперь вернуть подтверждение отправителю
			else:
				print(f'Получено что-то странное: {msg}')
				raise Exception
		except:
			print('Ошибка при получении')
			client.close()
			break
	client.close()


def get_users(msg):
	print(f'Получаем список пользователей...')
	users_raw = msg[len_header_b + len_command_b:]
	users_raw = users_raw.split(SEP)
	global users
	for user_raw in users_raw:
		if user_raw not in users and user_raw != '':
			users.append(user_raw)
	if len(users) == 0:
		print('Вы единственное подключение')
	else:
		print(f'Подключенные клиенты: {", ".join(users)}')


def service_send(msg):
	"""
	Заведомо меньше лимита
	"""
	client.send(f'{SERVICE}{msg}'.encode(FORMAT))


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
			print(f'{msg}\n')
			print(header)
			if header == SERVICE:
				# Смотрим, что следует за SERVICE
				reason = msg[len_header: len_header + len_command]
				print(reason)
				if reason == NICK_REQUEST:
					nickname = input(f'Введите свой псевдоним (не больше {floor(max_nickname_b / len("A".encode(FORMAT)))} символов): ')
					nickname_b = len(nickname.encode(FORMAT))
					if nickname_b <= max_nickname_b:
						service_send(nickname)
						# client.send(nickname_b)
					else:
						service_send(NICK_ERROR)
						# client.send(NICK_ERROR)
				elif reason == NICK_REQUEST_REP:
					print('Либо такой псевдоним уже существует, либо Вы превысили лимит\n')
					nickname = input('Введите другой: ')
					service_send(nickname)
					# client.send(nickname.encode(FORMAT))
				elif reason == NICK_APPROVED:
					print(f'Вы подключились к серверу как {nickname}')
				elif reason == USERS:
					get_users(msg)
					accepted = True
			# 	else:
			# 		print(f'Ну чет странное: {msg}\n')
			# else:
			# 	print(f'Ну чет очень странное: {msg}\n')
		except:
			print('Ошибка при задании псевдонима')
			client.close()
			return False
	return True


def start():
	if welcome():
		print('Готово к работе.')
		# Starting Threads For Listening And Writing
		receive_thread = threading.Thread(target=receive)
		receive_thread.start()

		write_thread = threading.Thread(target=send)
		write_thread.start()
	else:
		print('Все плохо')


start()
