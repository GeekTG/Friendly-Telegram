from .. import loader
import logging

logger = logging.getLogger(__name__)

def register(cb):
    cb(AFKMod())

class AFKMod(loader.Module):
    """Provides a message saying that you are unavailable (out of office)"""
    def __init__(self):
        self.commands = {}
        self.config = {}
        self.name = "AFK"
        self._me = None
    async def watcher(self, message):
        if self._me == None:
            self._me = await message.client.get_me()
        if message.mentioned or getattr(message.to_id, 'user_id', None) == self._me.id:
            logger.debug("tagged!")
            if await self.is_afk():
                await message.reply("<code>Sorry, I'm busy. But I'll read your message ASAP!</code>")

    async def is_afk(self):
        return False
