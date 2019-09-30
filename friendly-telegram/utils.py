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

import os
import logging
import asyncio
import functools
import shlex

from . import __main__
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from telethon.extensions import html


def get_args(message):
    try:
        message = message.message
    except AttributeError:
        pass
    if not message:
        return False
    return list(filter(lambda x: len(x) > 0, shlex.split(message, ' ')))[1:]


def get_args_raw(message):
    try:
        message = message.message
    except AttributeError:
        pass
    if not message:
        return False
    args = message.split(' ', 1)
    if len(args) > 1:
        return args[1]
    else:
        return ""


def get_args_split_by(message, s):
    m = get_args_raw(message)
    mess = m.split(s)
    return [st.strip() for st in mess]


def get_chat_id(message):
    chat = message.to_id
    attrs = vars(chat)
    if len(attrs) != 1:
        return None
    return next(iter(attrs.values()))


def escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escape_quotes(text):
    return escape_html(text).replace('"', "&quot;")


def get_base_dir():
    return get_dir(__main__.__file__)


def get_dir(mod):
    return os.path.abspath(os.path.dirname(os.path.abspath(mod)))


async def get_user(message):
    try:
        return await message.client.get_entity(message.from_id)
    except ValueError:  # Not in database. Lets go looking for them.
        logging.debug("user not in session cache. searching...")
    if isinstance(message.to_id, PeerUser):
        await message.client.get_dialogs()
        return await message.client.get_entity(message.from_id)
    elif isinstance(message.to_id, PeerChat) or isinstance(message.to_id, PeerChannel):
        async for user in message.client.iter_participants(message.to_id, aggressive=True):
            if user.id == message.from_id:
                return user
        logging.error("WTF! user isn't in the group where they sent the message")
        return None
    else:
        logging.error("WTF! to_id is not a user, chat or channel")
        return None


def run_sync(func, *args, **kwargs):
    # Returning a coro
    return asyncio.get_event_loop().run_in_executor(None, functools.partial(func, *args, **kwargs))


def run_async(loop, coro):
    # When we bump minimum support to 3.7, use run()
    return asyncio.run_coroutine_threadsafe(coro, loop).result()


def censor(obj, to_censor=["phone"], replace_with="redacted_{count}_chars"):
    """May modify the original object, but don't rely on it"""
    for k, v in vars(obj).items():
        if k in to_censor:
            setattr(obj, k, replace_with.format(count=len(v)))
        elif k[0] != "_" and hasattr(v, "__dict__"):
            setattr(obj, k, censor(v, to_censor, replace_with))
    return obj


def _fix_entities(ent, CONT_MSG, initial=False):
    for e in ent:
        e.offset -= 4096
        if initial:
            e.offset += len(CONT_MSG)
        else:
            e.length += len(CONT_MSG)
        if e.offset + e.length > 0:
            if e.offset < 0:
                e.offset = e.offset + 4096
                e.length = e.length - 4096
        elif e.offset < 0:
            e.length = 0  # We don't need this one, it doesn't reach.


async def answer(message, answer, **kwargs):
    CONT_MSG = "[continued]\n"
    ret = [message]
    if isinstance(answer, str) and not kwargs.get("asfile", False):
        txt, ent = html.parse(answer)
        await message.edit(html.unparse(txt[:4096], ent))
        txt = txt[4096:]
        _fix_entities(ent, CONT_MSG, True)
        while len(txt) > 0:
            txt = CONT_MSG + txt
            message.message = txt[:4096]
            message.entities = ent
            message.text = html.unparse(message.message, message.entities)
            txt = txt[4096:]
            _fix_entities(ent, CONT_MSG)
            ret.append(await message.respond(message, parse_mode="HTML", **kwargs))
    else:
        if message.media is not None:
            await message.edit(file=answer, **kwargs)
        else:
            await message.edit("<code>Loading media...</code>")
            ret = [await message.client.send_file(message.to_id, answer, reply_to=message.reply_to_msg_id, **kwargs)]
            await message.delete()
    return ret
