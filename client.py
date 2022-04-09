#!/usr/bin/env python3.9
import os
import signal
import socket
import sys
import threading

from help import *

SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)
users = []
nickname = ''


def send():
	"""
	Цикл для чтения информации вводимой пользователем и ее отправки.
	"""
	while True:
		show_info_text()
		text = input()
		if text == 'Users':
			client.send(MSG().set(SERVICE, tag=USERS))
		elif text in [headers, tags, flags]:
			print('Вы не можете отправить такое сообщение.')
		elif text in users:
			destination = text
			input_text_en = input('Введите сообщение').encode(FORMAT)
			len_input_text_en = len(input_text_en)
			# Предварительно посчитать длину сообщения
			len_prefix = len(f'{MSG_NORMAL}{destination}{SEP}{nickname}{SEP}{len_input_text_en}{SEP}'.encode(FORMAT))
			len_msg = len_prefix + len_input_text_en
			if len_msg <= MAX_LEN:
				msg = MSG().set(MSG_NORMAL, dest=destination, sender=nickname, text_en=input_text_en, len_text_b=len_input_text_en)
				if client.send(msg) == len_msg:
					print('Сообщение отправлено')
				else:
					print('Ошибка при отправке сообщения')
			else:
				send_smth_big(destination, len_prefix, input_text_en + MSG_BIG_END_flag.encode(FORMAT))
		else:
			print('Такого пользователя или команды не существует.')


def send_smth_big(destination: str, len_prefix: int, text_en: bytes):
	"""
	Если требуется отправить что-то большое, что не влезает в стандартный лимит.
	Считаем, сколько информации можно отправить, создаем генератор для отправки кусочков.
	"""
	print('Отправляем что-то большое')
	bytes_send = 0
	max_len_text = MAX_LEN - len_prefix
	# Добавляем в конец сигнал об окончании передачи большого сообщения
	text_pieces = (text_en[i: i + max_len_text] for i in range(0, len(text_en), max_len_text))
	for text_piece in text_pieces:
		bytes_send += client.send(MSG().set(MSG_BIG, dest=destination, sender=nickname, text_en=text_piece, len_text_b=len(text_en) - len(MSG_BIG_END_flag)))

	# Контролируем количество отправленных байт
	if bytes_send != len(text_en) + len_prefix * (len(text_en) // max_len_text + 1):
		print('Ошибка при отправке.\nПовторная отправка.')
		send_smth_big(destination, len_prefix, text_en)


def receive():
	"""
	Прием входящих сообщений.
	Читаем, анализиреум хедер.
	"""
	while True:
		try:
			msg = MSG().get(client.recv(MAX_LEN))
			if msg.header == SERVICE:
				if msg.tag == ADD:
					users.append(msg.data)
					print(f'Подключился новый клиент: {msg.data}')
				elif msg.tag == REMOVE:
					users.remove(msg.data)
					print(f'Клиент отключился: {msg.data}')
				elif msg.tag == USERS:
					get_users(msg)
				elif msg.tag == DISCONNECT:
					print('Вы были отключены')
					shutdown()
				elif msg.tag == MSG_CONTROL:
					# Прием оповещений о доставке/не доставке.
					if msg.flag == MSG_Y:
						print('Ваше сообщение доставлено')
					elif msg.flag == MSG_N:
						print('Ваше сообщение частично не доставлено')
				else:
					print(f'Получено сообщение с пометкой системное, не удалось обработать:\n{msg.tag}{msg.data}')
			elif msg.header == MSG_NORMAL:
				# Прием обычных сообщений
				if len(msg.text_en) == msg.len_text_b:
					print(f'Получено сообщение от {msg.sender}:\n{msg.text_en.decode(FORMAT)}')
					client.send(MSG().set(SERVICE, tag=MSG_CONTROL, dest=msg.sender, flag=MSG_Y, len_b=msg.len_text_b))
				else:
					print(f'Получено битое сообщение от {msg.sender}. Попытка расшифровать:\n{msg.text_en.decode(FORMAT)}')
					client.send(MSG().set(SERVICE, tag=MSG_CONTROL, dest=msg.sender, flag=MSG_N, len_b=msg.len_text_b))
			elif msg.header == MSG_BIG:
				# Прием изначально большого сообщения, разбитого на части.
				# Так как передаются байты, надо получить все исходное сообщение, а затем его декодировать.
				text_en = msg.text_en
				while True:
					new_msg = MSG().get(client.recv(MAX_LEN))
					if new_msg.destination == msg.destination and new_msg.sender == msg.sender:
						text_en += new_msg.text_en
						if new_msg.flag == MSG_BIG_END_flag:
							if len(text_en) == msg.len_text_b:
								print(f'Получено большое сообщение от {msg.sender}:\n{text_en.decode(FORMAT)}')
								client.send(MSG().set(SERVICE, tag=MSG_CONTROL, dest=msg.sender, flag=MSG_Y, len_b=msg.len_text_b))
							else:
								print(f'Получено битое сообщение от {msg.sender}.\n Получено {len(text_en)} из {msg.len_text_b} байт.')
								client.send(MSG().set(SERVICE, tag=MSG_CONTROL, dest=msg.sender, flag=MSG_N, len_b=msg.len_text_b))
							break
						print('q')
					else:
						print(f'Не получено большое сообщение от {msg.sender}.')
						client.send(MSG().set(SERVICE, tag=MSG_CONTROL, dest=msg.sender, flag=MSG_N, len_b=msg.len_text_b))
						break
					print('Принимаем...')
			else:
				print(f'Получено что-то странное.')
				raise Exception
			show_info_text()
		except:
			print('Ошибка при получении')
			shutdown()


def get_users(msg):
	"""
	Получение списка подключенных пользователей.
	"""
	print('Получаем список пользователей...')
	users_raw = msg.data.split(SEP)
	global users
	for user_raw in users_raw:
		if user_raw not in users and user_raw != '' and user_raw != nickname:
			users.append(user_raw)
	if len(users) == 0:
		print('Вы единственное подключение')
	else:
		print(f'Подключенные клиенты: {", ".join(users)}')
		print(f'Вы подключены как: {nickname}')


def show_info_text():
	print('\nВведите команду "Users" или адресата:')


def welcome():
	"""
	Вызывается только при подключении.
	Завершается при задании псевдонима и получения списка уже подключенных пользователей.
	"""
	def check(nick_input):
		if len(nick_input.encode(FORMAT)) <= max_nickname_b:
			client.send(MSG().set(SERVICE, tag=NICK, nick=nick_input))
		else:
			client.send(MSG().set(SERVICE, tag=NICK_ERROR))

	global nickname
	
	while True:
		try:
			msg = MSG().get(client.recv(MAX_LEN))
			if msg.header == SERVICE:
				if msg.tag == NICK_REQUEST:
					nick_input = input(f'Введите свой псевдоним (не больше {max_nickname_b // len("A".encode(FORMAT))} символов): ')
					check(nick_input)
				elif msg.tag == NICK_REQUEST_REP:
					print('Либо такой псевдоним уже существует, либо Вы превысили лимит\n')
					nick_input = input('Введите другой: ')
					check(nick_input)
				elif msg.tag == NICK_APPROVED:
					nickname = nick_input
					print(f'Вы подключились к серверу как {nickname}')
				elif msg.tag == USERS:
					get_users(msg)
					return
		except:
			print('Ошибка при задании псевдонима')
			shutdown()


def shutdown():
	client.close()
	print('Завершение работы')
	os.kill(os.getpid(), signal.SIGINT)
	sys.exit()


def start():
	"""
	Сначала запускается поток для представления пользователем.
	После завершения его работы (в случае принятия псевдонима) запускаются параллельные потоки приняти и отправки сообщений.
	"""
	try:
		welcome_thread = threading.Thread(target=welcome)
		welcome_thread.start()
		welcome_thread.join()

		receive_thread = threading.Thread(target=receive)
		receive_thread.start()

		write_thread = threading.Thread(target=send)
		write_thread.start()
	except:
		print('Все упало')
		shutdown()


if __name__ == '__main__':
	try:
		print('[STARTING]')
		start()
	except KeyboardInterrupt:
		shutdown()
