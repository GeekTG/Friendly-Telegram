import os
from . import __main__
def get_args(message):
    try:
        message = message.message
    except AttributeError:
        pass
    if not message:
        return False
    return list(filter(lambda x: len(x) > 0, message.split(' ')))[1:]

def get_args_raw(message):
    try:
        message = message.message
    except AttributeError:
        pass
    if not message:
        return False
    return message.split(' ', 1)[1]

def get_args_split_by(message, s):
    m = get_args_raw(message)
    mess = m.split(s)
    return [st.strip() for st in mess]

def get_chat_id(message):
    chat = message.to_id
    attrs = chat.__dict__
    if len(attrs) != 1:
        return None
    return next(iter(attrs.values()))

def escape_html(text):
    return text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

def get_base_dir():
    return os.path.relpath(os.path.dirname(__main__.__file__))
