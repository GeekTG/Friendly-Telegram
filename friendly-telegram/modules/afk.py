# -*- coding: future_fstrings -*-

from .. import loader, utils
import logging, asyncio

logger = logging.getLogger(__name__)

def register(cb):
    cb(AFKMod())

class AFKMod(loader.Module):
    """Provides a message saying that you are unavailable (out of office)"""
    def __init__(self):
        self.commands = {"afk":self.afkcmd, "unafk":self.unafkcmd}
        self.config = {}
        self.name = "AFK"
        self._me = None
        self._ratelimit = []

    async def client_ready(self, client, db):
        self._db = db
        self._me = await client.get_me()

    async def afkcmd(self, message):
        """.afk [message]
           If no message is provided, 'I'm AFK' will be used as default"""
        if utils.get_args_raw(message):
            self._db.set(__name__, "afk", utils.get_args_raw(message))
        else:
            self._db.set(__name__, "afk", True)
        await message.edit("<code>I'm AFK</code>")

    async def unafkcmd(self, message):
        """Remove the AFK status"""
        self._ratelimit.clear()
        self._db.set(__name__, "afk", False)
        await message.edit("<code>I'm no longer AFK</code>")

    async def watcher(self, message):
        if message.mentioned or getattr(message.to_id, 'user_id', None) == self._me.id:
            logger.debug("tagged!")
            if message.from_id in self._ratelimit:
                self._ratelimit.remove(message.from_id)
                return
            else:
                self._ratelimit += [message.from_id]
            user = await utils.get_user(message)
            if user.is_self or user.bot or user.verified:
                logger.debug("User is self, bot or verified.")
                return
            if self.get_afk() == True:
                await message.reply("<code>I'm AFK!</code>")
            elif self.get_afk() != False:
                await message.reply(f"<code>{utils.escape_html(self.get_afk())}</code>")

    def get_afk(self):
        return self._db.get(__name__, "afk", False)
