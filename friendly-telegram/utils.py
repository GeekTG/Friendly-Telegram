#    Friendly Telegram Userbot
#    by GeekTG Team

"""Utility functions to help modules do stuff"""

import os
import logging
import asyncio
import functools
import io
import shlex

import telethon
from telethon.tl.types import PeerUser, PeerChat, PeerChannel, MessageEntityMentionName, User, MessageMediaWebPage
from telethon.tl.custom.message import Message
from telethon.extensions import html

from . import __main__


def get_args(message):
    """Get arguments from message (str or Message), return list of arguments"""
    try:
        message = message.message
    except AttributeError:
        pass
    if not message:
        return False
    message = message.split(maxsplit=1)
    if len(message) <= 1:
        return []
    message = message[1]
    try:
        split = shlex.split(message)
    except ValueError:
        return message  # Cannot split, let's assume that it's just one long message
    return list(filter(lambda x: len(x) > 0, split))


def get_args_raw(message):
    """Get the parameters to the command as a raw string (not split)"""
    try:
        message = message.message
    except AttributeError:
        pass
    if not message:
        return False
    args = message.split(maxsplit=1)
    if len(args) > 1:
        return args[1]
    return ""


def get_args_split_by(message, sep):
    """Split args with a specific sep"""
    raw = get_args_raw(message)
    mess = raw.split(sep)
    return [section.strip() for section in mess if section]


def get_chat_id(message):
    """Get the chat ID, but without -100 if its a channel"""
    return telethon.utils.resolve_id(message.chat_id)[0]


def get_entity_id(entity):
    return telethon.utils.get_peer_id(entity)


def escape_html(text):
    """Pass all untrusted/potentially corrupt input here"""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escape_quotes(text):
    """Escape quotes to html quotes"""
    return escape_html(text).replace('"', "&quot;")


def get_base_dir():
    """Get directory of this file"""
    return get_dir(__main__.__file__)


def get_dir(mod):
    """Get directory of given module"""
    return os.path.abspath(os.path.dirname(os.path.abspath(mod)))


async def get_user(message):
    """Get user who sent message, searching if not found easily"""
    try:
        return await message.client.get_entity(message.sender_id)
    except ValueError:  # Not in database. Lets go looking for them.
        logging.debug("user not in session cache. searching...")
    if isinstance(message.to_id, PeerUser):
        try:
            await message.client.get_dialogs()
        except telethon.rpcerrorlist.BotMethodInvalid:
            return None
        return await message.client.get_entity(message.sender_id)
    if isinstance(message.to_id, (PeerChannel, PeerChat)):
        async for user in message.client.iter_participants(message.to_id, aggressive=True):
            if user.id == message.sender_id:
                return user
        logging.error("WTF! user isn't in the group where they sent the message")
        return None
    logging.error("WTF! to_id is not a user, chat or channel")
    return None


def run_sync(func, *args, **kwargs):
    """Run a non-async function in a new thread and return an awaitable"""
    # Returning a coro
    return asyncio.get_event_loop().run_in_executor(None, functools.partial(func, *args, **kwargs))


def run_async(loop, coro):
    """Run an async function as a non-async function, blocking till it's done"""
    # When we bump minimum support to 3.7, use run()
    return asyncio.run_coroutine_threadsafe(coro, loop).result()


def censor(obj, to_censor=["phone"], replace_with="redacted_{count}_chars"):  # pylint: disable=W0102
    # Safe to disable W0102 because we don't touch to_censor, mutably or immutably.
    """May modify the original object, but don't rely on it"""
    for k, v in vars(obj).items():
        if k in to_censor:
            setattr(obj, k, replace_with.format(count=len(v)))
        elif k[0] != "_" and hasattr(v, "__dict__"):
            setattr(obj, k, censor(v, to_censor, replace_with))
    return obj


def relocate_entities(entities, offset, text=None):
    """Move all entities by offset (truncating at text)"""
    if text is not None:
        length = len(text)
    for ent in entities.copy() if entities else ():
        ent.offset += offset
        if ent.offset < 0:
            ent.length += ent.offset
            ent.offset = 0
        if text is not None and ent.offset + ent.length > length:
            ent.length = length - ent.offset
        if ent.length <= 0:
            entities.remove(ent)
    return entities


def _fix_entities(ent, cont_msg, initial=False):
    for entity in ent:
        if not initial:
            entity.offset -= len(cont_msg)
            entity.length += len(cont_msg)
        if entity.offset + entity.length - 4096 < 0:
            entity.offset = 0
            entity.length = 0  # It's useless
            continue
        already_done = max(4096 - entity.offset, 0)
        entity.offset = max(entity.offset - 4096, 0)
        entity.length -= already_done
        entity.offset += len(cont_msg)


async def answer(message, response, **kwargs):
    """Use this to give the response to a command"""
    if isinstance(message, list):
        delete_job = asyncio.ensure_future(message[0].client.delete_messages(message[0].input_chat, message[1:]))
        message = message[0]
    else:
        delete_job = None
    if await message.client.is_bot() and isinstance(response, str) and len(response) > 4096:
        kwargs.setdefault("asfile", True)
    kwargs.setdefault("link_preview", False)
    cont_msg = "[continued]\n"
    edit = message.out
    if not edit:
        kwargs.setdefault("reply_to", message.reply_to_msg_id if await message.get_reply_message() else message.id)
    parse_mode = telethon.utils.sanitize_parse_mode(kwargs.pop("parse_mode", message.client.parse_mode))
    if isinstance(response, str) and not kwargs.pop("asfile", False):
        txt, ent = parse_mode.parse(response)
        logging.debug(txt)
        logging.debug(ent)
        ret = [await (message.edit if edit else message.respond)(txt[:4096], parse_mode=lambda t: (t, ent), **kwargs)]
        txt = txt[4096:]
        _fix_entities(ent, cont_msg, True)
        while len(txt) > 0:
            txt = cont_msg + txt
            message.message = txt[:4096]
            message.entities = ent
            message.text = html.unparse(message.message, message.entities)
            txt = txt[4096:]
            _fix_entities(ent, cont_msg)
            ret.append(await (message.reply if edit else message.respond)(message,
                                                                          parse_mode=lambda t: (t, ent), **kwargs))
    elif isinstance(response, Message):
        if message.media is None and (response.media is None or isinstance(response.media, MessageMediaWebPage)):
            ret = (await message.edit(response.message,
                                      parse_mode=lambda t: (t, response.entities or []),
                                      link_preview=isinstance(response.media, MessageMediaWebPage)),)
        else:
            txt = "<b>Loading message...</b>"
            new = await (message.edit if edit else message.reply)(txt)
            ret = (await message.respond(response, **kwargs),)
            await new.delete()
    else:
        if isinstance(response, bytes):
            response = io.BytesIO(response)
        if isinstance(response, str):
            response = io.BytesIO(response.encode("utf-8"))
        name = kwargs.pop("filename", None)
        if name:
            response.name = name
        if message.media is not None and edit:
            await message.edit(file=response, **kwargs)
        else:
            txt = "<b>Loading media...</b>"  # TODO translations
            new = await (message.edit if edit else message.reply)(txt)
            kwargs.setdefault("reply_to", message.reply_to_msg_id if await message.get_reply_message() else message.id)
            ret = (await message.client.send_file(message.chat_id, response,
                                                  **kwargs),)
            await new.delete()
    if delete_job:
        await delete_job
    return ret


async def get_target(message, arg_no=0):
    if any(isinstance(ent, MessageEntityMentionName) for ent in (message.entities or [])):
        e = sorted(filter(lambda x: isinstance(x, MessageEntityMentionName),
                          message.entities), key=lambda x: x.offset)[0]
        return e.user_id
    elif len(get_args(message)) > arg_no:
        user = get_args(message)[arg_no]
    elif message.is_reply:
        return (await message.get_reply_message()).sender_id
    elif hasattr(message.to_id, "user_id"):
        user = message.to_id.user_id
    else:
        return None
    try:
        ent = await message.client.get_entity(user)
    except ValueError:
        return None
    else:
        if isinstance(ent, User):
            return ent.id
