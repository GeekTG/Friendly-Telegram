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
import os
import sys
import argparse
import asyncio
import json
import functools
import collections
import sqlite3
import importlib
import shlex

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors.rpcerrorlist import PhoneNumberInvalidError, MessageNotModifiedError, ApiIdInvalidError
from telethon.tl.functions.channels import DeleteChannelRequest

from . import utils, loader


from .database import backend, frontend
from .translations.core import Translator

importlib.import_module(".modules", __package__)  # Required on 3.5 only


class MemoryHandler(logging.Handler):
    """Keeps 2 buffers. One for dispatched messages. One for unused messages. When the length of the 2 together is 100
       truncate to make them 100 together, first trimming handled then unused."""
    def __init__(self, target, capacity):
        super().__init__(0)
        self.target = target
        self.capacity = capacity
        self.buffer = []
        self.handledbuffer = []
        self.lvl = logging.WARNING

    def setLevel(self, level):
        self.lvl = level

    def dump(self):
        """Return a list of logging entries"""
        return self.handledbuffer + self.buffer

    def dumps(self, lvl=0):
        """Return all entries of minimum level as list of strings"""
        return [self.target.format(record) for record in (self.buffer + self.handledbuffer) if record.levelno >= lvl]

    def emit(self, record):
        if len(self.buffer) + len(self.handledbuffer) >= self.capacity:
            if self.handledbuffer:
                del self.handledbuffer[0]
            else:
                del self.buffer[0]
        self.buffer.append(record)
        if record.levelno >= self.lvl and self.lvl >= 0:
            self.acquire()
            try:
                for precord in self.buffer:
                    self.target.handle(precord)
                self.handledbuffer = self.handledbuffer[-(self.capacity - len(self.buffer)):] + self.buffer
                self.buffer = []
            finally:
                self.release()


_formatter = logging.Formatter(logging.BASIC_FORMAT, "")  # pylint: disable=C0103
_handler = logging.StreamHandler()  # pylint: disable=C0103
_handler.setFormatter(_formatter)
logging.getLogger().addHandler(MemoryHandler(_handler, 500))
logging.getLogger().setLevel(0)
logging.captureWarnings(True)


async def handle_command(modules, db, event):
    """Handle all commands"""
    prefix = db.get(__name__, "command_prefix", False) or "."  # Empty string evaluates to False, so the `or` activates
    if not hasattr(event, "message") or getattr(event.message, "message", "") == "":
        return
    if event.message.message[0:len(prefix)] != prefix:
        return
    logging.debug("Incoming command!")
    if not event.message:
        logging.debug("Ignoring command with no text.")
        return
    if event.via_bot_id:
        logging.debug("Ignoring inline bot.")
        return
    message = utils.censor(event.message)
    blacklist_chats = db.get(__name__, "blacklist_chats", [])
    if utils.get_chat_id(message) in blacklist_chats or message.from_id is None:
        logging.debug("Message is blacklisted")
        return
    if len(message.message) > len(prefix) and message.message[:len(prefix) * 2] == prefix * 2 \
            and message.message != len(message.message) // len(prefix) * prefix:
        # Allow escaping commands using .'s
        await message.edit(utils.escape_html(message.message[len(prefix):]))
    logging.debug(message)
    # Make sure we don't get confused about spaces or other shit in the prefix
    message.message = message.message[len(prefix):]
    try:
        shlex.split(message.message)
    except ValueError as e:
        await message.edit("Invalid Syntax: " + str(e))
        return
    if not message.message:
        return  # Message is just the prefix
    command = message.message.split(maxsplit=1)[0]
    logging.debug(command)
    coro = modules.dispatch(command, message)  # modules.dispatch is not a coro, but returns one
    if coro is not None:
        try:
            await coro
        except Exception as e:
            logging.exception("Command failed")
            try:
                await message.edit("<code>Request failed! Request was " + message.message
                                   + ". Please report it in the support group (`.support`) "
                                   + "with the logs (`.logs error`)</code>")
            finally:
                raise e


async def handle_incoming(modules, db, event):
    """Handle all incoming messages"""
    logging.debug("Incoming message!")
    message = utils.censor(event.message)
    logging.debug(message)
    blacklist_chats = db.get(__name__, "blacklist_chats", [])
    if utils.get_chat_id(message) in blacklist_chats:
        logging.debug("Message is blacklisted")
        return
    for fun in modules.watchers:
        try:
            await fun(message)
        except Exception:
            logging.exception("Error running watcher")


def run_config(db, phone=None, modules=None):
    """Load configurator.py"""
    from . import configurator
    return configurator.run(db, phone, phone is None, modules)


def parse_arguments():
    """Parse the arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", "-s", action="store_true")
    parser.add_argument("--phone", "-p", action="append")
    parser.add_argument("--token", "-t", action="append", dest="tokens")
    parser.add_argument("--heroku", action="store_true")
    parser.add_argument("--translate", action="store_true")
    arguments = parser.parse_args()
    logging.debug(arguments)
    if sys.platform == 'win32':
        # Subprocess support; not needed in 3.8 but not harmful
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    return arguments


def get_phones(arguments):
    """Get phones from the --token, --phone, and environment"""
    phones = set(arguments.phone if arguments.phone else [])
    phones.update(map(lambda f: f[18:-8],
                      filter(lambda f: f.startswith("friendly-telegram-") and f.endswith(".session"),
                             os.listdir(os.path.dirname(utils.get_base_dir())))))

    authtoken = os.environ.get("authorization_strings", False)  # for heroku
    if authtoken and not arguments.setup:
        try:
            authtoken = json.loads(authtoken)
        except json.decoder.JSONDecodeError:
            logging.warning("authtoken invalid")
            authtoken = False

    if arguments.tokens and not authtoken:
        authtoken = {}
    if arguments.tokens:
        for token in arguments.tokens:
            phone = sorted(phones).pop(0)
            phones.remove(phone)  # Handled seperately by authtoken logic
            authtoken.update(**{phone: token})
    return phones, authtoken


def get_api_token():
    """Get API Token from disk or environment"""
    while True:
        try:
            from . import api_token
        except ImportError:
            try:
                api_token = collections.namedtuple("api_token", ["ID", "HASH"])(os.environ["api_id"],
                                                                                os.environ["api_hash"])
            except KeyError:
                run_config({})
            else:
                return api_token
        else:
            return api_token


def main():
    """Main entrypoint"""
    arguments = parse_arguments()

    if arguments.translate:
        from .translations import translateutil
        translateutil.ui()
        return

    clients = []
    phones, authtoken = get_phones(arguments)
    api_token = get_api_token()
    if api_token is None:
        return

    if authtoken:
        for phone, token in authtoken.items():
            try:
                clients += [TelegramClient(StringSession(token), api_token.ID, api_token.HASH,
                                           connection_retries=None).start(phone)]
            except ValueError:
                run_config({})
                return
            clients[-1].phone = phone  # for consistency
    if len(clients) == 0 and len(phones) == 0:
        phones = [input("Please enter your phone: ")]
    for phone in phones:
        try:
            clients += [TelegramClient(StringSession() if arguments.heroku else
                                       os.path.join(os.path.dirname(utils.get_base_dir()), "friendly-telegram"
                                                    + (("-" + phone) if phone else "")), api_token.ID,
                                       api_token.HASH, connection_retries=None).start(phone)]
        except sqlite3.OperationalError as ex:
            print("Error initialising phone " + (phone if phone else "unknown") + " " + ",".join(ex.args)  # noqa: T001
                  + ": this is probably your fault. Try checking that this is the only instance running and "
                  "that the session is not copied. If that doesn't help, delete the file named '"
                  "friendly-telegram" + (("-" + phone) if phone else "") + ".session'")
            continue
        except (ValueError, ApiIdInvalidError):
            # Bad API hash/ID
            run_config({})
            return
        except PhoneNumberInvalidError:
            print("Please check the phone number. Use international format (+XX...)"  # noqa: T001
                  " and don't put spaces in it.")
            continue
        clients[-1].phone = phone  # so we can format stuff nicer in configurator

    if arguments.heroku:
        key = input("Please enter your Heroku API key (from https://dashboard.heroku.com/account): ").strip()
        from . import heroku
        heroku.publish(clients, key, api_token)
        print("Installed to heroku successfully! Type .help in Telegram for help.")  # noqa: T001
        return

    loops = [amain(client, clients, arguments.setup) for client in clients]

    asyncio.get_event_loop().set_exception_handler(lambda _, x:
                                                   logging.error("Exception on event loop! %s", x["message"],
                                                                 exc_info=x["exception"]))
    asyncio.get_event_loop().run_until_complete(asyncio.gather(*loops))


async def amain(client, allclients, setup=False):
    """Entrypoint for async init, run once for each user"""
    async with client:
        client.parse_mode = "HTML"
        await client.start()
        [handler] = logging.getLogger().handlers
        if setup:
            db = backend.CloudBackend(client)
            await db.init(lambda e: None)
            jdb = await db.do_download()
            try:
                pdb = json.loads(jdb)
            except (json.decoder.JSONDecodeError, TypeError):
                pdb = {}
            modules = loader.Modules()
            modules.register_all(Translator())
            fdb = frontend.Database(None)
            await fdb.init()
            modules.send_config(fdb)
            await modules.send_ready(client, fdb, allclients)  # Allow normal init even in setup
            handler.setLevel(50)
            pdb = run_config(pdb, getattr(client, "phone", "Unknown Number"), modules)
            if pdb is None:
                await client(DeleteChannelRequest(db.db))
                return
            try:
                await db.do_upload(json.dumps(pdb))
            except MessageNotModifiedError:
                pass
            return
        db = frontend.Database(backend.CloudBackend(client))
        await db.init()
        logging.debug("got db")
        logging.info("Loading logging config...")
        handler.setLevel(db.get(__name__, "loglevel", logging.WARNING))

        babelfish = Translator(db.get(__name__, "language", ["en"]))

        modules = loader.Modules()
        modules.register_all(babelfish)

        modules.send_config(db)
        await modules.send_ready(client, db, allclients)
        client.add_event_handler(functools.partial(handle_incoming, modules, db),
                                 events.NewMessage(incoming=True))
        client.add_event_handler(functools.partial(handle_command, modules, db),
                                 events.NewMessage(outgoing=True, forwards=False))
        print("Started for " + str((await client.get_me(True)).user_id))  # noqa: T001
        await client.run_until_disconnected()
