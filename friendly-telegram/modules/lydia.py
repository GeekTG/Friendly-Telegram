# Some parts are Copyright (C) Diederik Noordhuis (@AntiEngineer) 2019
# All licensed under project license

# The API is not yet public. To get a key, go to https://t.me/Intellivoid then ask Qián Zhào.

from .. import loader, utils
import logging, asyncio, requests, time, random
from telethon import functions, types

logger = logging.getLogger(__name__)

def register(cb):
    cb(LydiaMod())

class LydiaAPI():
    endpoint = "http://enterprise-sla2.api.intellivoid.info/coffeehouse/v2"

    class APIError(ValueError):
        pass
    class ApiSuspendedError(APIError):
        pass
    class InvalidApiKeyError(APIError):
        pass
    class AIError(APIError):
        pass
    class SessionInvalidError(APIError):
        pass
    class SessionNotFoundError(APIError):
        pass

    def __init__(self, api_key):
        self.api_key = api_key

    async def create_session(self, language=None):
        payload = {
            "api_key": self.api_key,
        }
        if not language is None:
            payload["language"] = language
        response = (await utils.run_sync(requests.post, self.endpoint + "/createSession", payload)).json()
        if response["code"] != 200:
            if response["code"] == 403:
                raise self.ApiSuspendedError(response["message"])
            if response["code"] == 401:
                raise self.InvalidApiKeyError(response["message"])
            raise self.APIError(response["message"])
        return response["payload"]

    async def think(self, session_id, data):
        payload = {
            "api_key": self.api_key,
            "session_id": session_id,
            "input": data
        }
        response = (await utils.run_sync(requests.post, self.endpoint + "/thinkThought", payload)).json()
        if response["code"] != 200:
            if response["code"] == 503:
                raise self.AIError(response["message"])
            if response["code"] == 400:
                raise self.SessionInvalidError(response["message"])
            if response["code"] == 404:
                raise self.SessionNotFoundError(response["message"])
            raise self.APIError(response["message"])
        return response["payload"]

class LydiaMod(loader.Module):
    """Talks to a robot instead of a human"""
    def __init__(self):
        self.commands = {"enlydia":self.enablelydiacmd, "dislydia":self.disablelydiacmd}
        self.config = {"CLIENT_KEY":""}
        self.name = "Lydia anti-PM"
        self._ratelimit = []
        self._cleanup = None

    async def client_ready(self, client, db):
        self._db = db
        self._lydia = LydiaAPI(self.config["CLIENT_KEY"])
        self._me = await client.get_me()
        # Schedule cleanups
        self._cleanup = asyncio.ensure_future(self.schedule_cleanups())

    async def schedule_cleanups(self):
        """Cleans up dead sessions and reschedules itself to run when the next session expiry takes place"""
        if not self._cleanup is None:
            self._cleanup.cancel()
        sessions = self._db.get(__name__, "sessions", {})
        if len(sessions) == 0:
            return
        nsessions = {}
        t = time.time()
        for ident, session in sessions.items():
            if not session["expires"] < t:
                nsessions.update({ident:session})
        next = min(*[v["expires"] for k,v in nsessions.items()])
        if nsessions != sessions:
            self._db.set(__name__, "sessions", nsessions)
        # Don't worry about the 1 day limit below 3.7.1, if it isn't expired we will just reschedule, as nothing will be matched for deletion.
        await asyncio.sleep(min(next - t, 86399))

        await self.schedule_cleanups()

    async def enablelydiacmd(self, message):
        """Enables Lydia for target user"""
        old = self._db.get(__name__, "allow", [])
        if message.is_reply:
            user = (await message.get_reply_message()).from_id
        else:
            user = getattr(message.to_id, "user_id", None)
        if user is None:
            await message.edit("<code>The AI service cannot be enabled or disabled in this chat. Is this a group chat?</code>")
            return
        try:
            old.remove(user)
            self._db.set(__name__, "allow", old)
        except ValueError:
            await message.edit("<code>The AI service cannot be enabled for this user. Perhaps it wasn't disabled to begin with?</code>")
            return
        await message.edit("<code>AI enabled for this user. </code>")

    async def disablelydiacmd(self, message):
        """Disables Lydia for the target user"""
        if message.is_reply:
            user = (await message.get_reply_message()).from_id
        else:
            user = getattr(message.to_id, "user_id", None)
        if user is None:
            await message.edit("<code>The AI service cannot be enabled or disabled in this chat. Is this a group chat?</code>")
            return
        self._db.set(__name__, "allow", self._db.get(__name__, "allow", [])+[user])
        msg = await message.edit("<code>AI disabled for this user.</code>")

    async def watcher(self, message):
        if self.config["CLIENT_KEY"] == "":
            logger.debug("no key set for lydia, returning")
            return
        if getattr(message.to_id, 'user_id', None) == self._me.id:
            logger.debug("pm'd!")
            user = await utils.get_user(message)
            if user.is_self or user.bot or user.verified:
                logger.debug("User is self, bot or verified.")
                return
            if self.get_allowed(message.from_id):
                logger.debug("PM received from user who is not using AI service")
            else:
                await message.client(functions.messages.SetTypingRequest(
                    peer=await utils.get_user(message),
                    action=types.SendMessageTypingAction()
                ))
                try:
                    # Get a session
                    sessions = self._db.get(__name__, "sessions", {})
                    session = sessions.get(message.from_id, None)
                    if session is None or session["expires"] < time.time():
                        session = await self._lydia.create_session()
                        logger.debug(session)
                        sessions[message.from_id] = session
                        logger.debug(sessions)
                        self._db.set(__name__, "sessions", sessions)
                        if not self._cleanup is None:
                            self._cleanup.cancel()
                        self._cleanup = asyncio.ensure_future(self.schedule_cleanups())
                    logger.debug(session)
                    # AI Response method
                    msg = message.message if isinstance(message.message, str) else " "
                    airesp = await self._lydia.think(session["session_id"], str(msg))
                    logger.debug("AI says %s", airesp)
                    if random.randint(0, 1):
                        await message.respond(airesp["output"])
                    else:
                        await message.reply(airesp["output"])
                finally:
                    await message.client(functions.messages.SetTypingRequest(
                        peer=await utils.get_user(message),
                        action=types.SendMessageCancelAction()
                    ))

    def get_allowed(self, id):
        return id in self._db.get(__name__, "allow", [])
