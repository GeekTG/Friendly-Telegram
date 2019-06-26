# Some parts are Copyright (C) Diederik Noordhuis (@AntiEngineer) 2019
# All licensed under project license

# The API is not yet public. To get a key, go to https://t.me/Intellivoid then ask Qián Zhào.

from .. import loader, utils
import logging, asyncio, requests, asyncio, functools, hashlib
from telethon import functions, types

logger = logging.getLogger(__name__)

def register(cb):
    cb(LydiaMod())

class LydiaAPI():

    def __init__(self, client_key):
        self.endpoint = "https://api.intellivoid.info/coffeehouse/v1"
        self.client_key = client_key

    async def think(self, user_id, data):
        sha1 = hashlib.sha1()
        sha1.update(user_id.to_bytes((user_id.bit_length() + 7) // 8, "big"))
        payload = {
            "client_key": self.client_key,
            "user_id": sha1.hexdigest(),
            "input": data
        }
        response = await asyncio.get_event_loop().run_in_executor(None, functools.partial(requests.post, self.endpoint + "/ThinkTelegramThought", payload))

        return response.json()["payload"]["output"]

class LydiaMod(loader.Module):
    """Talks to a robot instead of a human"""
    def __init__(self):
        self.commands = {"enlydia":self.enablelydiacmd, "dislydia":self.disablelydiacmd}
        self.config = {"CLIENT_KEY":""}
        self.name = "Lydia anti-PM"
        self._ratelimit = []

    async def client_ready(self, client, db):
        self._db = db
        self._lydia = LydiaAPI(self.config["CLIENT_KEY"])
        self._me = await client.get_me()

    async def enablelydiacmd(self, message):
        """Enables Lydia for target user"""
        old = self._db.get(__name__, "allow", [])
        if message.is_reply:
            user = (await message.get_reply_message()).from_id
        else:
            user = getattr(message.to_id, "user_id", None)
        if user is None:
            await message.edit("<code>The AI service cannot be enabled or disabled in this chat. Is this a group chat?</code>", parse_mode="HTML")
            return
        try:
            old.remove(user)
            self._db.set(__name__, "allow", old)
        except ValueError:
            await message.edit("<code>The AI service cannot be enabled for this user. Perhaps it wasn't disabled to begin with?</code>")
            return
        await message.edit("<code>AI enabled for this user. </code>", parse_mode="HTML")

    async def disablelydiacmd(self, message):
        """Disables Lydia for the target user"""
        if message.is_reply:
            user = (await message.get_reply_message()).from_id
        else:
            user = getattr(message.to_id, "user_id", None)
        if user is None:
            await message.edit("<code>The AI service cannot be enabled or disabled in this chat. Is this a group chat?</code>", parse_mode="HTML")
            return
        self._db.set(__name__, "allow", self._db.get(__name__, "allow", [])+[user])
        msg = await message.edit("<code>AI disabled for this user.</code>", parse_mode="HTML")

    async def watcher(self, message):
        if self.config["CLIENT_KEY"] == "":
            logging.debug("no key set for lydia, returning")
            return
        if getattr(message.to_id, 'user_id', None) == self._me.id:
            logger.debug("pm'd!")
            if message.from_id in self._ratelimit:
                self._ratelimit.remove(message.from_id)
            else:
                self._ratelimit += [message.from_id]
            if self.get_allowed(message.from_id):
                logger.debug("PM received from user who is not using AI service")
            else:
                await message.client(functions.messages.SetTypingRequest(
                    peer=await utils.get_user(message),
                    action=types.SendMessageTypingAction()
                ))
                try:
                    # AI Response method
                    msg = message.message if isinstance(message.message, str) else ""
                    await message.respond(await self._lydia.think(message.from_id, str(msg)))
                finally:
                    await message.client(functions.messages.SetTypingRequest(
                        peer=await utils.get_user(message),
                        action=types.SendMessageCancelAction()
                    ))

    def get_allowed(self, id):
        return id in self._db.get(__name__, "allow", [])
