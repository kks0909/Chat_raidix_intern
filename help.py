# HEADER = 64
MAX_LEN = 1024
max_nickname_b = 64
PORT = 5050
FORMAT = 'UTF-8'

# Хедеры: с чего может начинаться сообщение
MSG_tag = '<MSG_____>'
MSG_BIG_tag = '<MSGBIG__>'
SERVICE = '<SERVICE_>'
MSG_CONTROL = '<MSGCONTR>'
headers = [MSG_tag, MSG_BIG_tag, SERVICE, MSG_CONTROL]
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
MSG_Y = '<MSG_YES_>'
MSG_N = '<MSG_NOPE>'

tags = [NICK, NICK_REQUEST, NICK_ERROR, NICK_REQUEST_REP, NICK_APPROVED, ADD, REMOVE, USERS, MSG_Y, MSG_N]
len_tag = len(max(tags, key=len))
len_tag_b = len_tag * len('A'.encode(FORMAT))


# Передается в тексте а не в тегах
MSG_BIG_END_flag = '<MSG_BIG_END>'

# Разделитель
SEP = '<SEP>'



