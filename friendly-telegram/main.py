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

class MemoryHandler(logging.Handler):
    """Keeps 2 buffers. One for dispatched messages. One for unused messages.
       When the length of the 2 together is > 100, truncate to make them 100 together, first trimming handled then unused."""
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
        return self.handledbuffer + self.buffer
    def dumps(self, lvl=0):
        return [self.target.format(record) for record in (self.buffer+self.handledbuffer) if record.levelno >= lvl]
    def emit(self, record):
        if len(self.buffer) + len(self.handledbuffer) >= self.capacity:
            if len(self.handledbuffer):
                del self.handledbuffer[0]
            else:
                del self.buffer[0]
        self.buffer.append(record)
        if record.levelno >= self.lvl and self.lvl >= 0:
            self.acquire()
            try:
                for record in self.buffer:
                    self.target.handle(record)
                self.handledbuffer = self.handledbuffer[-(self.capacity-len(self.buffer)):] + self.buffer
                self.buffer = []
            finally:
                self.release()
formatter = logging.Formatter(logging.BASIC_FORMAT, "")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.getLogger().addHandler(MemoryHandler(handler, 500))
logging.getLogger().setLevel(0)

import os, sys, argparse, asyncio, json, functools, atexit, collections

from telethon import TelegramClient, sync, events
from telethon.errors.rpcerrorlist import PhoneNumberInvalidError, MessageNotModifiedError

from . import utils, loader, __main__

from .database import backend, frontend

async def handle_command(modules, db, event):
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
    if (utils.get_chat_id(message) in blacklist_chats or (whitelist_chats and not utils.get_chat_id(message) in whitelist_chats)) and not utils.get_chat_id(message) == message.from_id:
        logging.debug("Message is blacklisted or not in whitelist")
        return
    if len(message.message) > 1 and message.message[:2] == ".." and message.message != len(message.message) * ".":
        # Allow escaping commands using .'s
        await message.edit(utils.escape_html(message.message[1:]))
    logging.debug(message)
    command = message.message.split(' ',1)[0]
    logging.debug(command)
    coro = modules.dispatch(command, message) # modules.dispatch is not a coro, but returns one
    if not coro is None:
        try:
            await coro
        except Exception as e:
            try:
                await message.edit("<code>Request failed! Request was " + message.message + ". Please report it in the support group (`.support`) with the logs (`.logs error`)</code>")
            finally:
                raise e

async def handle_incoming(modules, db, event):
    logging.debug("Incoming message!")
    message = utils.censor(event.message)
    logging.debug(message)
    blacklist_chats = db.get(__name__, "blacklist_chats", [])
    whitelist_chats = db.get(__name__, "whitelist_chats", [])
    if (utils.get_chat_id(message) in blacklist_chats or (whitelist_chats and not utils.get_chat_id(message) in whitelist_chats)) and not utils.get_chat_id(message) == message.from_id:
        logging.debug("Message is blacklisted or not in whitelist")
        return
    for fun in modules.watchers:
        try:
            await fun(message)
        except:
            logging.exception("Error running watcher")

def run_config(db, phone=None):
    from . import configurator
    return configurator.run(db, phone, phone == None)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", "-s", action="store_true")
    parser.add_argument("--config", "-c", action="append")
    parser.add_argument("--value", "-v", action="append")
    parser.add_argument("--phone", "-p", action="append")
    parser.add_argument("--heroku", action="store_true")
    arguments = parser.parse_args()
    logging.debug(arguments)

    if sys.platform == 'win32':
        # Subprocess support
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    clients = []

    phones = arguments.phone if arguments.phone else []
    phones += set(map(lambda f: f[18:-8], filter(lambda f: f[:19] == "friendly-telegram-+" and f[-8:] == ".session", os.listdir(os.path.dirname(utils.get_base_dir())))))

    authtoken = os.environ.get("authorization_strings", False) # for heroku

    if arguments.heroku:
        from telethon.sessions import StringSession
        session_name = lambda phone: StringSession()
    else:
        session_name = lambda phone: os.path.join(os.path.dirname(utils.get_base_dir()), "friendly-telegram" + (("-"+phone) if phone else ""))

    try:
        from . import api_token
    except ImportError:
        try:
            api_token = collections.namedtuple("api_token", ["ID", "HASH"])(os.environ["api_id"], os.environ["api_hash"])
        except KeyError:
            run_config({})
            return
    if authtoken:
        from telethon.sessions import StringSession
        for phone, token in json.loads(authtoken).items():
            clients += [TelegramClient(StringSession(token), api_token.ID, api_token.HASH, connection_retries=None).start(phone)]
            clients[-1].phone = phone # for consistency
    if os.path.isfile(os.path.join(os.path.dirname(utils.get_base_dir()), 'friendly-telegram.session')):
        clients += [TelegramClient(session_name(None), api_token.ID, api_token.HASH).start()]
        print("You're using the legacy session format. Please contact support, this will break in a future update.")
    if len(clients) == 0 and len(phones) == 0:
        phones += [input("Please enter your phone: ")]
    for phone in phones:
        try:
            clients += [TelegramClient(session_name(phone), api_token.ID, api_token.HASH, connection_retries=None).start(phone)]
            clients[-1].phone = phone # so we can format stuff nicer in configurator
        except PhoneNumberInvalidError:
            print("Please check the phone number. Use international format (+XX...) and don't put spaces in it.")
            return

    if arguments.heroku:
        key = input("Please enter your Heroku API key: ").strip()
        data = {getattr(client, "phone", ""): client.session.save() for client in clients}
        import heroku3
        heroku = heroku3.from_key(key)
        print("Configuring...")
        app = heroku.create_app(stack_id_or_name='heroku-18', region_id_or_name="us")
        config = app.config()
        config["authorization_strings"] = json.dumps(data)
        from . import api_token
        config["api_id"] = api_token.ID
        config["api_hash"] = api_token.HASH
        from git import Repo
        repo = Repo(os.path.dirname(utils.get_base_dir()))
        if "heroku" in repo.remotes:
            remote = repo.remote("heroku")
        else:
            remote = repo.create_remote("heroku", app.git_url.replace("https://", "https://api:" + key + "@"))
        print("Pushing...")
        remote.push(refspec='HEAD:refs/heads/master')
        print("Pushed")
        app.scale_formation_process("worker", 1)
        print("Scaled! Test your bot with .ping")
        return

    cfg = arguments.config if arguments.config else []
    vlu = arguments.value if arguments.value else []

    loops = []
    for client in clients:
        atexit.register(client.disconnect)
        loops += [amain(client, dict(zip(cfg, vlu)), clients, arguments.setup)]

    asyncio.get_event_loop().set_exception_handler(lambda _, x: logging.error("Exception on event loop! %s", x["message"], exc_info=x["exception"]))

    asyncio.get_event_loop().run_until_complete(asyncio.gather(*loops))

async def amain(client, cfg, allclients, setup=False):
    async with client as c:
        await c.start()
        await client.catch_up()
        c.parse_mode = "HTML"
        if setup:
            db = backend.CloudBackend(c)
            await db.init(lambda e: None)
            jdb = await db.do_download()
            try:
                pdb = json.loads(jdb)
            except:
                pdb = {}
            pdb = run_config(pdb, getattr(c, 'phone', "Unknown Number"))
            try:
                await db.do_upload(json.dumps(pdb))
            except MessageNotModifiedError:
                pass
            return
        db = frontend.Database(backend.CloudBackend(c))
        await db.init()
        logging.debug("got db")
        logging.info("Loading logging config...")
        [handler] = logging.getLogger().handlers
        handler.setLevel(db.get(__name__, "loglevel", logging.WARNING))

        modules = loader.Modules()
        modules.register_all(db.get(__name__, "disable_modules", []))

        blacklist_chats = db.get(__name__, "blacklist_chats", [])
        whitelist_chats = db.get(__name__, "whitelist_chats", [])
        modules.send_config(db, cfg)
        await modules.send_ready(client, db, allclients)
        client.add_event_handler(functools.partial(handle_incoming, modules, db), events.NewMessage(incoming=True, forwards=False))
        client.add_event_handler(functools.partial(handle_command, modules, db), events.NewMessage(outgoing=True, forwards=False, pattern=r'\..*'))
        print("Started")
        await c.run_until_disconnected()
