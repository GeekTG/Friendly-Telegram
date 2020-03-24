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
import signal
import shlex

from telethon import TelegramClient, events
from telethon.sessions import StringSession, SQLiteSession
from telethon.errors.rpcerrorlist import PhoneNumberInvalidError, MessageNotModifiedError, ApiIdInvalidError
from telethon.tl.functions.channels import DeleteChannelRequest

from . import utils, loader


from .database import backend, local_backend, frontend
from .translations.core import Translator

try:
    from .web import core
except ImportError:
    web_available = False
    logging.error("Unable to import web")
else:
    web_available = True


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
        self.lvl = logging.WARNING  # Default loglevel

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
logging.getLogger().handlers = []
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
    whitelist_chats = db.get(__name__, "whitelist_chats", [])
    whitelist_modules = db.get(__name__, "whitelist_modules", [])
    if utils.get_chat_id(message) in blacklist_chats or (whitelist_chats and utils.get_chat_id(message) not in
                                                         whitelist_chats) or message.from_id is None:
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
    txt, func = modules.dispatch(command)
    message.message = txt + message.message[len(command):]
    if func is not None:
        if str(utils.get_chat_id(message)) + "." + func.__self__.__module__ in blacklist_chats:
            logging.debug("Command is blacklisted in chat")
            return
        if whitelist_modules and not (str(utils.get_chat_id(message)) + "."
                                      + func.__self__.__module__ in whitelist_modules):
            logging.debug("Command is not whitelisted in chat")
            return
        try:
            await func(message)
        except Exception as e:
            logging.exception("Command failed")
            try:
                await message.edit("<b>Request failed! Request was</b> <code>" + utils.escape_html(message.message)
                                   + "</code><b>. Please report it in the support group (</b><code>{0}support</code>"
                                   "<b>) along with the logs (</b><code>{0}logs error</code><b>)</b>".format(prefix))
            finally:
                raise e


async def handle_incoming(modules, db, event):
    """Handle all incoming messages"""
    logging.debug("Incoming message!")
    message = utils.censor(event.message)
    blacklist_chats = db.get(__name__, "blacklist_chats", [])
    whitelist_chats = db.get(__name__, "whitelist_chats", [])
    whitelist_modules = db.get(__name__, "whitelist_modules", [])
    if utils.get_chat_id(message) in blacklist_chats or (whitelist_chats and utils.get_chat_id(message) not in
                                                         whitelist_chats) or message.from_id is None:
        logging.debug("Message is blacklisted")
        return
    for func in modules.watchers:
        if str(utils.get_chat_id(message)) + "." + func.__self__.__module__ in blacklist_chats:
            logging.debug("Command is blacklisted in chat")
            return
        if whitelist_modules and not (str(utils.get_chat_id(message)) + "."
                                      + func.__self__.__module__ in whitelist_modules):
            logging.debug("Command is not whitelisted in chat")
            return
        try:
            await func(message)
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
    parser.add_argument("--local-db", dest="local", action="store_true")
    parser.add_argument("--web-only", dest="web_only", action="store_true")
    parser.add_argument("--no-web", dest="web", action="store_false")
    parser.add_argument("--heroku-web-internal", dest="heroku_web_internal", action="store_true",
                        help="This is for internal use only. If you use it, things will go wrong.")
    arguments = parser.parse_args()
    logging.debug(arguments)
    if sys.platform == "win32":
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

    if arguments.setup or (arguments.tokens and not authtoken):
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
                api_token = collections.namedtuple("api_token", ("ID", "HASH"))(os.environ["api_id"],
                                                                                os.environ["api_hash"])
            except KeyError:
                return None
            else:
                return api_token
        else:
            return api_token


def sigterm(signum, handler):
    # This ensures that we call atexit hooks and close FDs when Heroku kills us un-gracefully
    sys.exit(143)  # SIGTERM + 128


def main():  # noqa: C901
    """Main entrypoint"""
    arguments = parse_arguments()
    loop = asyncio.get_event_loop()

    clients = []
    phones, authtoken = get_phones(arguments)
    api_token = get_api_token()

    if web_available:
        web = core.Web(api_token=api_token) if arguments.web else None
    else:
        if arguments.heroku_web_internal:
            raise RuntimeError("Web required but unavailable")
        web = None

    if api_token is None:
        if web:
            loop.run_until_complete(web.start())
            print("Web mode ready for configuration")  # noqa: T001
            if not arguments.heroku_web_internal:
                print("Please visit http://localhost:" + str(web.port))  # noqa: T001
            loop.run_until_complete(web.wait_for_api_token_setup())
            api_token = web.api_token
        else:
            run_config({})

    if authtoken:
        for phone, token in authtoken.items():
            try:
                clients += [TelegramClient(StringSession(token), api_token.ID, api_token.HASH,
                                           connection_retries=None).start(phone)]
            except ValueError:
                run_config({})
                return
            clients[-1].phone = phone  # for consistency
    if not clients and not phones:
        if web:
            if not web.running.is_set():
                loop.run_until_complete(web.start())
                print("Web mode ready for configuration")  # noqa: T001
                if not arguments.heroku_web_internal:
                    print("Please visit http://localhost:" + str(web.port))  # noqa: T001
            loop.run_until_complete(web.wait_for_clients_setup())
            arguments.heroku = web.heroku_api_token
            clients = web.clients
            for client in clients:
                if arguments.heroku:
                    session = StringSession()
                else:
                    session = SQLiteSession(os.path.join(os.path.dirname(utils.get_base_dir()),
                                                         "friendly-telegram-" + client.phone))
                session.set_dc(client.session.dc_id, client.session.server_address, client.session.port)
                session.auth_key = client.session.auth_key
                if not arguments.heroku:
                    session.save()
                client.session = session
        else:
            try:
                phones = [input("Please enter your phone: ")]
            except EOFError:
                print()  # noqa: T001
                print("=" * 30)  # noqa: T001
                print()  # noqa: T001
                print("Hello. If you are seeing this, it means YOU ARE DOING SOMETHING WRONG!")  # noqa: T001
                print()  # noqa: T001
                print("It is likely that you tried to deploy to heroku - "  # noqa: T001
                      "you cannot do this via the web interface.")
                print("To deploy to heroku, go to "  # noqa: T001
                      "https://friendly-telegram.gitlab.io/heroku to learn more")
                print()  # noqa: T001
                print("In addition, you seem to have forked the friendly-telegram repo. THIS IS WRONG!")  # noqa: T001
                print("You should remove the forked repo, and read https://friendly-telegram.gitlab.io")  # noqa: T001
                print()  # noqa: T001
                print("If you're not using Heroku, then you are using a non-interactive prompt but "  # noqa: T001
                      "you have not got a session configured, meaning authentication to Telegram is "
                      "impossible.")  # noqa: T001
                print()  # noqa: T001
                print("THIS ERROR IS YOUR FAULT. DO NOT REPORT IT AS A BUG!")  # noqa: T001
                print("Goodbye.")  # noqa: T001
                sys.exit(1)
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
        if isinstance(arguments.heroku, str):
            key = arguments.heroku
        else:
            key = input("Please enter your Heroku API key (from https://dashboard.heroku.com/account): ").strip()
        from . import heroku
        app = heroku.publish(clients, key, api_token)
        print("Installed to heroku successfully! Type .help in Telegram for help.")  # noqa: T001
        if web:
            web.redirect_url = app.web_url
            web.ready.set()
            loop.run_until_complete(web.root_redirected.wait())
        return

    if arguments.heroku_web_internal:
        signal.signal(signal.SIGTERM, sigterm)

    loops = [amain(client, clients, web, arguments) for client in clients]

    loop.set_exception_handler(lambda _, x:
                               logging.error("Exception on event loop! %s", x["message"], exc_info=x["exception"]))
    loop.run_until_complete(asyncio.gather(*loops))


async def amain(client, allclients, web, arguments):
    """Entrypoint for async init, run once for each user"""
    setup = arguments.setup
    local = arguments.local
    web_only = arguments.web_only
    async with client:
        client.parse_mode = "HTML"
        await client.start()
        [handler] = logging.getLogger().handlers
        dbc = local_backend.LocalBackend if local else backend.CloudBackend
        if setup:
            db = dbc(client)
            await db.init(lambda e: None)
            jdb = await db.do_download()
            try:
                pdb = json.loads(jdb)
            except (json.decoder.JSONDecodeError, TypeError):
                pdb = {}
            modules = loader.Modules()
            babelfish = Translator([])
            await babelfish.init(client)
            modules.register_all(babelfish)
            fdb = frontend.Database(dbc(client), True)
            await fdb.init()
            modules.send_config(fdb, babelfish)
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
        db = frontend.Database(dbc(client))
        await db.init()
        logging.debug("got db")
        logging.info("Loading logging config...")
        handler.setLevel(db.get(__name__, "loglevel", logging.WARNING))

        babelfish = Translator(db.get(__name__, "langpacks", []), db.get(__name__, "language", ["en"]))
        await babelfish.init(client)

        modules = loader.Modules()
        modules.register_all(babelfish)

        modules.send_config(db, babelfish)
        await modules.send_ready(client, db, allclients)
        if not web_only:
            client.add_event_handler(functools.partial(handle_incoming, modules, db),
                                     events.NewMessage(incoming=True))
            client.add_event_handler(functools.partial(handle_command, modules, db),
                                     events.NewMessage(outgoing=True, forwards=False))
        print("Started for " + str((await client.get_me(True)).user_id))  # noqa: T001
        if web:
            await web.add_loader(client, modules, db)
            await web.start_if_ready(len(allclients))
        await client.run_until_disconnected()
