# HEADER = 64
MAX_LEN = 1024
max_nickname_b = 64
PORT = 5050
FORMAT = 'UTF-8'

# Хедеры: с чего может начинаться сообщение
MSG_NORMAL = '<MSG_____>'
MSG_BIG = '<MSGBIG__>'
SERVICE = '<SERVICE_>'
headers = [MSG_NORMAL, MSG_BIG, SERVICE]
len_header = len(max(headers, key=len))
len_header_b = len_header * len('A'.encode(FORMAT))


# Теги, которые могут следовать за заголовком SERVICE
NICK = '<NICKNAME>'
NICK_REQUEST = '<NICK_REQ>'
NICK_ERROR = '<NICK_ERR>'
NICK_REQUEST_REP = '<NICK_REP>'
NICK_APPROVED = '<NICK_ACC>'
ADD = '<ADD_____>'
REMOVE = '<REMOVE__>'
USERS = '<USERS___>'
DISCONNECT = '<DISCONN_>'
MSG_CONTROL = '<MSGCONTR>'

tags = [NICK, NICK_REQUEST, NICK_ERROR, NICK_REQUEST_REP, NICK_APPROVED, ADD, REMOVE, USERS, MSG_CONTROL]
len_tag = len(max(tags, key=len))
len_tag_b = len_tag * len('A'.encode(FORMAT))


# Передается в тексте а не в тегах
MSG_Y = '<MSG_YES>'
MSG_N = '<MSG_NOPE>'
MSG_BIG_END_flag = '<MSG_BIG_END>'
flags = [MSG_Y, MSG_N, MSG_BIG_END_flag]

# Разделитель
SEP = '<SEP>'


class MSG:
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

	def get(self, msg):
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

	def set(self, header, **data):
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
			# self.len_msg_b = len(message) - len(SEP)
			# self.len_msg_b += len(str(self.len_msg_b).encode(FORMAT))
			# message = message.replace(f'{SEP}{SEP}{SEP}'.encode(FORMAT), f'{SEP}{self.len_msg_b}{SEP}'.encode(FORMAT), 1)
		# elif self.header == MSG_BIG:
		# 	message += f"{data['dest']}{SEP}{data['sender']}{SEP}{SEP}{SEP}"
		# 	message = message.encode(FORMAT) + data['text_en']
		# 	self.len_msg_b = len(message) - len(SEP)
		# 	self.len_msg_b += len(str(self.len_msg_b).encode(FORMAT))
		# 	message = message.replace(f'{SEP}{SEP}{SEP}'.encode(FORMAT), f'{SEP}{self.len_msg_b}{SEP}'.encode(FORMAT), 1)
		return message
