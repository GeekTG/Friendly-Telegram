from .. import loader
import logging
from telethon.tl.types import PeerUser

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
        self._ratelimit = {}

    async def client_ready(self, client, db):
        self._db = db
        self._me = await client.get_me()

    async def afkcmd(self, message):
        self._db.set(__name__, "afk", True)
        await message.edit("<code>I'm AFK</code>", parse_mode="HTML")

    async def unafkcmd(self, message):
        self._db.set(__name__, "afk", False)
        await message.edit("<code>I'm no longer AFK</code>", parse_mode="HTML")

    async def watcher(self, message):
        if message.mentioned or getattr(message.to_id, 'user_id', None) == self._me.id:
            logger.debug("tagged!")
            if message.from_id in self._ratelimit.keys():
                await asyncio.sleep(self._ratelimit[message.from_id]/2)
                self._ratelimit[message.from_id] = self._ratelimit[message.from_id] * 1.5
            else:
                self._ratelimit[message.from_id] = 1
            if await self.is_afk():
                await message.reply("<code>I'm AFK!</code>", parse_mode="HTML")

    async def is_afk(self):
        return self._db.get(__name__, "afk")
