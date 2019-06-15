# -*- coding: future_fstrings -*-

from .. import loader, utils
import logging, asyncio
from telethon import functions, types

logger = logging.getLogger(__name__)

def register(cb):
    cb(AntiPMMod())

class AntiPMMod(loader.Module):
    """Provides a message saying that you are unavailable (out of office)"""
    def __init__(self):
        self.commands = {"allow":self.allowcmd, "report":self.reportcmd}
        self.config = {}
        self.name = "Anti PM"
        self._me = None
        self._ratelimit = []

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._me = await client.get_me()

    async def allowcmd(self, message):
        if message.is_reply:
            user = (await message.get_reply_message()).from_id
        else:
            user = getattr(message.to_id, "user_id", None)
        if not user:
            await message.edit("<code>Who shall I allow to PM?</code>", parse_mode="HTML")
            return
        self._db.set(__name__, "allow", self._db.get(__name__, "allow", [])+[user])
        await message.edit("<code>PM Authorised</code>", parse_mode="HTML")

    async def reportcmd(self, message):
        """Report the user spam. Use only in PM"""
        old = self._db.get(__name__, "allow", [])
        try:
            old.remove(getattr(message.to_id, "user_id", None))
            self._db.set(__name__, "allow", old)
        except ValueError:
            pass
        await self._client(functions.account.ReportPeerRequest(peer=message.to_id, reason=types.InputReportReasonSpam()))
        msg = await message.edit("<code>You just got reported spam!</code>", parse_mode="HTML")
#        await msg.delete(revoke=False)

    async def watcher(self, message):
        if getattr(message.to_id, 'user_id', None) == self._me.id:
            logger.debug("pm'd!")
            if message.from_id in self._ratelimit:
                self._ratelimit.remove(message.from_id)
                return
            else:
                self._ratelimit += [message.from_id]
            user = await utils.get_user(message)
            if user.is_self or user.bot or user.verified:
                logging.debug("User is self, bot or verified.")
                return
            if self.get_allowed(message.from_id):
                logger.debug("Authorised pm detected")
            else:
                await message.respond(f"<code>Please do not PM me. You will get reported spam.</code>")

    def get_allowed(self, id):
        return id in self._db.get(__name__, "allow", [])
