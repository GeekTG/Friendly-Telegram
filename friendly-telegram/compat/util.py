#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging

from telethon.extensions import markdown

logger = logging.getLogger(__name__)

COMMAND_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789_"


def get_cmd_name(pattern):
    """Get the first word out of a regex, hoping that it is easy to parse"""
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
        logger.info("Unable to register for non-command-based outgoing messages, pattern=%s", pattern)
        return False
    # Find first non-alpha character and get all chars before it
    i = 0
    cmd = ""
    while i < len(pattern) and pattern[i] in COMMAND_CHARS:
        i += 1
        cmd = pattern[:i]
    if not cmd:
        logger.info("Unable to identify command correctly, i=%d, pattern=%s", i, pattern)
        return False
    return cmd


class MarkdownBotPassthrough():
    """Passthrough class that forces markdown mode"""
    def __init__(self, under):
        self.__under = under

    def __edit(self, *args, **kwargs):
        if "parse_mode" not in kwargs:
            logger.debug("Forcing markdown for edit")
            kwargs.update(parse_mode="Markdown")
        return type(self)(self.__under.edit(*args, **kwargs))

    def __send_message(self, *args, **kwargs):
        if "parse_mode" not in kwargs:
            logger.debug("Forcing markdown for send_message")
            kwargs.update(parse_mode="Markdown")
        return type(self)(self.__under.send_message(*args, **kwargs))

    def __reply(self, *args, **kwargs):
        if "parse_mode" not in kwargs:
            logger.debug("Forcing markdown for send_message")
            kwargs.update(parse_mode="Markdown")
        return type(self)(self.__under.reply(*args, **kwargs))

    def __respond(self, *args, **kwargs):
        if "parse_mode" not in kwargs:
            logger.debug("Forcing markdown for send_message")
            kwargs.update(parse_mode="Markdown")
        return type(self)(self.__under.respond(*args, **kwargs))

    def __send_file(self, *args, **kwargs):
        if "parse_mode" not in kwargs:
            logger.debug("Forcing markdown for send_file")
            kwargs.update(parse_mode="Markdown")
        return type(self)(self.__under.send_message(*args, **kwargs))

    async def __get_reply_message(self, *args, **kwargs):
        ret = await self.__under.get_reply_message(*args, **kwargs)
        if ret is not None:
            ret.text = markdown.unparse(ret.message, ret.entities)
        return type(self)(ret)

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        if name == "edit":
            return self.__edit
        if name == "send_message":
            return self.__send_message
        if name == "reply":
            return self.__reply
        if name == "respond":
            return self.__respond
        if name == "get_reply_message":
            return self.__get_reply_message
        if name == "client":
            return type(self)(self.__under.client)  # Recurse
        return getattr(self.__under, name)

    def __setattr__(self, name, value):
        self.__dict__[name] = value

    def __call__(self, *args, **kwargs):
        return self.__under.__call__(*args, **kwargs)
