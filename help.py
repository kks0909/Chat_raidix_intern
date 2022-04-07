# HEADER = 64
MAX_LEN = 1024
max_nickname_b = 64
PORT = 5050
FORMAT = 'UTF-8'

# Хедеры: с чего может начинаться сообщение
MSG_tag = '<MSG____>'
MSG_BIG_tag = '<MSGBIG_>'
SERVICE = '<SERVICE>'
headers = [MSG_tag, MSG_BIG_tag, SERVICE]
len_header = len(max(headers, key=len))
len_header_b = len_header * len('A'.encode(FORMAT))


# Теги, которые могут следовать за заголовком SERVICE
NICK_REQUEST = '<NICK_REQ___>'
NICK_ERROR = '<NICK_ERROR_>'
NICK_REQUEST_REP = '<NICK_AGAIN_>'
NICK_APPROVED = '<NICK_ACCEPT>'
ADD = '<ADD________>'
REMOVE = '<REMOVE_____>'
USERS = '<USERS______>'
service_commands = [NICK_REQUEST, NICK_ERROR, NICK_REQUEST_REP, NICK_APPROVED, ADD, REMOVE, USERS]
len_command = len(max(service_commands, key=len))
len_command_b = len_command * len('A'.encode(FORMAT))


# Передается в тексте а не в тегах
MSG_BIG_END_flag = '<MSG_BIG_END>'

# Разделитель
SEP = '<SEP>'



