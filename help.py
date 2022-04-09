# Константы, которые можно при необходимости изменять
MAX_LEN = 1024  # По докуметации: достаточно небольшая степень 2, например 4096.
max_nickname_b = 64
PORT = 5050
FORMAT = 'UTF-8'


"""
Дальнейшее не подлежит изменению, тк это используется в структуре передаваемых сообщений.
MSG(header[, tag[, flag]])
Например:
f'{MSG_NORMAL}dest_nick{SEP}sender_nick{SEP}len_text_b{SEP}text'
f'{MSG_BIG}dest_nick{SEP}sender_nick{SEP}len_text_b{SEP}text_part{MSG_BIG_END_flag}'
f'{SERVICE}{ADD}text'
f'{SERVICE}{NICK_REQUEST}'
"""

# Хедеры: с чего может начинаться сообщение
MSG_NORMAL = '<MSG_____>'  # Обычное, укладывающееся в лимит сообщение
MSG_BIG = '<MSGBIG__>'  # Большое, отправляемое по частям сообщение
SERVICE = '<SERVICE_>'  # Сервисное сообщение
headers = [MSG_NORMAL, MSG_BIG, SERVICE]
len_header = len(max(headers, key=len))
len_header_b = len_header * len('A'.encode(FORMAT))


# Теги, которые могут следовать за заголовком SERVICE
NICK = '<NICKNAME>'  # для передачи псевдонима; + nickname
NICK_REQUEST = '<NICK_REQ>'  # для запроса сервером псевдонима пользователя
NICK_ERROR = '<NICK_ERR>'  # для пометки ошибки при задании псевдонима
NICK_REQUEST_REP = '<NICK_REP>'  # для повторного запроса сервером псевдонима пользователя
NICK_APPROVED = '<NICK_ACC>'  # для подтверждения сервером псевдонима
ADD = '<ADD_____>'  # для оповещения о новом подключенном пользователе; + nickname
REMOVE = '<REMOVE__>'  # для оповещения об отключении пользователя; + nickname
USERS = '<USERS___>'  # для передачи списка пользователей
DISCONNECT = '<DISCONN_>'  # для оповещении пользователя об его отключении
MSG_CONTROL = '<MSGCONTR>'  # для системных сообщений о доставке

tags = [NICK, NICK_REQUEST, NICK_ERROR, NICK_REQUEST_REP, NICK_APPROVED, ADD, REMOVE, USERS, MSG_CONTROL]
len_tag = len(max(tags, key=len))
len_tag_b = len_tag * len('A'.encode(FORMAT))


# Передается в тексте а не в тегах
MSG_Y = '<MSG_YES>'  # для подтверждения доставки
MSG_N = '<MSG_NOPE>'  # для подтверждения недоставки
MSG_BIG_END_flag = '<MSG_BIG_END>' # для отметки конца 'большого' сообщения, передаваемого по частям
flags = [MSG_Y, MSG_N, MSG_BIG_END_flag]

# Разделитель
SEP = '<SEP>'


class MSG:
	"""
	Структура для сообщений.
	"""
	def __init__(self):
		self.header = None
		self.tag = None
		self.data = None
		self.text_en = None
		self.destination = None
		self.sender = None
		self.len_text_b = None
		self.flag = None

		self.msg = None

	def get(self, msg: bytes):
		"""
		Геттер для получения информации из полученного сообщения.
		"""
		self.msg = msg
		self.header = self.msg[: len_header_b].decode(FORMAT)
		if self.header == SERVICE:
			self.tag = self.msg[len_header_b: len_header_b + len_tag_b].decode(FORMAT)
			if self.tag in [NICK, USERS, ADD, REMOVE]:
				self.data = self.msg[len_header_b + len_tag_b:].decode(FORMAT)
			elif self.tag == MSG_CONTROL:
				self.destination, self.flag, self.len_text_b = (item.decode(FORMAT) for item in self.msg[len_header_b + len_tag_b:].split(SEP.encode(FORMAT)))
				self.len_text_b = int(self.len_text_b)
		elif self.header in [MSG_NORMAL, MSG_BIG]:
			self.destination, self.sender, self.len_text_b, self.text_en = self.msg[len_header_b:].split(SEP.encode(FORMAT))
			self.destination, self.sender, self.len_text_b = (item.decode(FORMAT) for item in [self.destination, self.sender, self.len_text_b])
			self.len_text_b = int(self.len_text_b)
			if self.header == MSG_BIG and self.text_en.endswith(MSG_BIG_END_flag.encode(FORMAT)):
				self.flag = MSG_BIG_END_flag
				self.text_en = self.text_en[:-len(MSG_BIG_END_flag.encode(FORMAT))]
		return self

	def set(self, header, **data) -> bytes:
		"""
		Сеттер для создания сообщения по заданным параметрам.
		"""
		self.header = header
		message = header
		if self.header == SERVICE:
			self.tag = data['tag']
			message += self.tag
			if self.tag in [NICK, USERS, ADD, REMOVE] and data.get('nick') is not None:
				message += data['nick']
			elif self.tag == MSG_CONTROL:
				message += f"{data['dest']}{SEP}{data['flag']}{SEP}"
				self.len_text_b = len(message.encode(FORMAT))
				self.len_text_b += len(str(self.len_text_b).encode(FORMAT))
				message += str(self.len_text_b)
			message = message.encode(FORMAT)
		elif self.header in [MSG_NORMAL, MSG_BIG]:
			message += f"{data['dest']}{SEP}{data['sender']}{SEP}{data['len_text_b']}{SEP}"
			message = message.encode(FORMAT) + data['text_en']
		return message
