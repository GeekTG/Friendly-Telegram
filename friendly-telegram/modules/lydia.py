# Some parts are Copyright (C) Diederik Noordhuis (@AntiEngineer) 2019
# All licensed under project license

# The API is not yet public. To get a key, go to https://t.me/Intellivoid then ask Qián Zhào.

from .. import loader, utils
import logging, asyncio, requests, hashlib
from telethon import functions, types

logger = logging.getLogger(__name__)

def register(cb):
    cb(LydiaMod())

class LydiaAPI():
    endpoint = "https://api.intellivoid.info/coffeehouse/v2"

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
                    if session is None or session["expires"]:
                        session = await self._lydia.create_session()
                        logger.debug(session)
                        sessions[message.from_id] = session
                        logger.debug(sessions)
                        self._db.set(__name__, "sessions", sessions)
                    logger.debug(session)
                    # AI Response method
                    msg = message.message if isinstance(message.message, str) else " "
                    airesp = await self._lydia.think(session["session_id"], str(msg))
                    logger.debug("AI says %s", airesp)
                    await message.respond(airesp)
                finally:
                    await message.client(functions.messages.SetTypingRequest(
                        peer=await utils.get_user(message),
                        action=types.SendMessageCancelAction()
                    ))

    def get_allowed(self, id):
        return id in self._db.get(__name__, "allow", [])
