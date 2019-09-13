# Some parts are Copyright (C) Diederik Noordhuis (@AntiEngineer) 2019
# All licensed under project license

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

# The API is not yet public. To get a key, go to https://t.me/Intellivoid then ask Qián Zhào.

from .. import loader, utils
import logging
import asyncio
import time
import random
import coffeehouse
from telethon import functions, types

logger = logging.getLogger(__name__)


def register(cb):
    cb(LydiaMod())


class LydiaMod(loader.Module):
    """Talks to a robot instead of a human"""
    def __init__(self):
        self.config = loader.ModuleConfig("CLIENT_KEY", "", "The API key for lydia, acquire from @IntellivoidDev")
        self.name = _("Lydia anti-PM")
        self._ratelimit = []
        self._cleanup = None

    async def client_ready(self, client, db):
        self._db = db
        self._lydia = coffeehouse.API(self.config["CLIENT_KEY"])
        self._me = await client.get_me()
        # Schedule cleanups
        self._cleanup = asyncio.ensure_future(self.schedule_cleanups())

    async def schedule_cleanups(self):
        """Cleans up dead sessions and reschedules itself to run when the next session expiry takes place"""
        if self._cleanup is not None:
            self._cleanup.cancel()
        sessions = self._db.get(__name__, "sessions", {})
        if len(sessions) == 0:
            return
        nsessions = {}
        t = time.time()
        for ident, session in sessions.items():
            if not session["expires"] < t:
                nsessions.update({ident: session})
            else:
                session = self._lydia.get_session(session["id"])
                if session["available"]:
                    nsessions.update({ident: session})
        if len(nsessions):
            next = min(*[v["expires"] for k, v in nsessions.items()])
        else:
            next = 86399
        if nsessions != sessions:
            self._db.set(__name__, "sessions", nsessions)
        # Don't worry about the 1 day limit below 3.7.1, if it isn't expired we will just reschedule,
        # as nothing will be matched for deletion.
        await asyncio.sleep(min(next - t, 86399))

        await self.schedule_cleanups()

    async def enlydiacmd(self, message):
        """Enables Lydia for target user"""
        old = self._db.get(__name__, "allow", [])
        if message.is_reply:
            user = (await message.get_reply_message()).from_id
        else:
            user = getattr(message.to_id, "user_id", None)
        if user is None:
            await message.edit(_("<code>The AI service cannot be enabled or disabled in this chat. "
                                 + "Is this a group chat?</code>"))
            return
        try:
            old.remove(user)
            self._db.set(__name__, "allow", old)
        except ValueError:
            await message.edit(_("<code>The AI service cannot be enabled for this user. Perhaps it wasn't disabled "
                                 + "to begin with?</code>"))
            return
        await message.edit(_("<code>AI enabled for this user. </code>"))

    async def forcelydiacmd(self, message):
        """Enables Lydia for user in groups"""
        if message.is_reply:
            user = (await message.get_reply_message()).from_id
        else:
            user = getattr(message.to_id, "user_id", None)
        if user is None:
            await message.edit(_("<code>The AI service cannot be enabled or disabled in this chat. "
                                 + "Is this a group chat?</code>"))
            return
        self._db.set(__name__, "force", self._db.get(__name__, "force", []) + [user])
        await message.edit(_("<code>AI enabled for this user in groups.</code>"))

    async def dislydiacmd(self, message):
        """Disables Lydia for the target user"""
        if message.is_reply:
            user = (await message.get_reply_message()).from_id
        else:
            user = getattr(message.to_id, "user_id", None)
        if user is None:
            await message.edit(_("<code>The AI service cannot be enabled or disabled in this chat. "
                                 + "Is this a group chat?</code>"))
            return
        self._db.set(__name__, "allow", self._db.get(__name__, "allow", []) + [user])
        old = self._db.get(__name__, "force", [])
        try:
            old.remove(user)
            self._db.set(__name__, "force", old)
        except ValueError:
            pass
        await message.edit(_("<code>AI disabled for this user.</code>"))

    async def watcher(self, message):
        if self.config["CLIENT_KEY"] == "":
            logger.debug("no key set for lydia, returning")
            return
        if (isinstance(message.to_id, types.PeerUser) and not self.get_allowed(message.from_id)) or \
                (self.get_forced(message.from_id) and not isinstance(message.to_id, types.PeerUser)):
            user = await utils.get_user(message)
            if user.is_self or user.bot or user.verified:
                logger.debug("User is self, bot or verified.")
                return
            else:
                if not isinstance(message.message, str):
                    return
                if len(message.message) == 0:
                    return
                await message.client(functions.messages.SetTypingRequest(
                    peer=await utils.get_user(message),
                    action=types.SendMessageTypingAction()
                ))
                try:
                    # Get a session
                    sessions = self._db.get(__name__, "sessions", {})
                    session = sessions.get(utils.get_chat_id(message), None)
                    if session is None or session["expires"] < time.time():
                        session = await utils.run_sync(self._lydia.create_session)
                        session = {"session_id": session.id, "expires": session.expires}
                        logger.debug(session)
                        sessions[utils.get_chat_id(message)] = session
                        logger.debug(sessions)
                        self._db.set(__name__, "sessions", sessions)
                        if self._cleanup is not None:
                            self._cleanup.cancel()
                        self._cleanup = asyncio.ensure_future(self.schedule_cleanups())
                    logger.debug(session)
                    # AI Response method
                    msg = message.message
                    airesp = await utils.run_sync(self._lydia.think_thought, session["session_id"], str(msg))
                    logger.debug("AI says %s", airesp)
                    if random.randint(0, 1) and isinstance(message.to_id, types.PeerUser):
                        await message.respond(airesp)
                    else:
                        await message.reply(airesp)
                finally:
                    await message.client(functions.messages.SetTypingRequest(
                        peer=await utils.get_user(message),
                        action=types.SendMessageCancelAction()
                    ))

    def get_allowed(self, id):
        return id in self._db.get(__name__, "allow", [])

    def get_forced(self, id):
        return id in self._db.get(__name__, "force", [])
