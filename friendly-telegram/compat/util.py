import logging

logger = logging.getLogger(__name__)

COMMAND_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789_"


def get_cmd_name(pattern):
    # Find command string: ugly af :)
    logger.debug(pattern)
    if pattern == "(?i)":
        pattern = pattern[4:]
    if pattern[0] == "^":
        pattern = pattern[1:]
    if pattern[0] == ".":
        # That seems to be the normal command prefix
        pattern = pattern[1:]
    elif pattern[:2] == r"\.":
        # That seems to be the normal command prefix
        pattern = pattern[2:]
    else:
        logger.error("Unable to register for non-command-based outgoing messages, pattern=" + pattern)
        return False
    # Find first non-alpha character and get all chars before it
    i = 0
    cmd = ""
    while i < len(pattern) and pattern[i] in COMMAND_CHARS:
        i += 1
        cmd = pattern[:i]
    if not len(cmd):
        logger.error("Unable to identify command correctly, i=" + str(i) + ", pattern=" + pattern)
        return False
    return cmd


class MarkdownBotPassthrough():
    def __init__(self, under):
        self.__under = under

    def __edit(self, *args, **kwargs):
        logger.debug("Forcing markdown for edit")
        kwargs.update(parse_mode="Markdown")
        return self.__under.edit(*args, **kwargs)

    def __send_message(self, *args, **kwargs):
        logger.debug("Forcing markdown for send_message")
        kwargs.update(parse_mode="Markdown")
        return self.__under.send_message(*args, **kwargs)

    def __send_file(self, *args, **kwargs):
        logger.debug("Forcing Markdown for send_file")
        kwargs.update(parse_mode="Markdown")
        return self.__under.send_message(*args, **kwargs)

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        if name == "edit":
            return self.__edit
        if name == "send_message":
            return self.__send_message
        if name == "client":
            return type(self)(self.__under.client)  # Recurse
        return getattr(self.__under, name)

    def __setattr__(self, name, value):
        self.__dict__[name] = value

    def __call__(self, *args, **kwargs):
        self.__under.__call__(*args, **kwargs)
