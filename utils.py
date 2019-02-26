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
    print(message.split(' ', 1)[1])
    return message.split(' ', 1)[1]
