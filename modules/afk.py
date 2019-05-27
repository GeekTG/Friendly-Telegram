from .. import loader
import logging

def register(cb):
    logging.debug('registering %s', __file__)
    cb(AFKMod())

class AFKMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {}
        self.config = {}
        self.name = "AFK"
        self.help = "Provides a message saying that you are unavailable (out of office)"
        self._me = None
    async def watcher(self, message):
        if self._me == None:
            self._me = await message.client.get_me()
        if message.mentioned or getattr(message.to_id, 'user_id', None) == self._me.id:
            logging.debug("tagged!")
            if await self.is_afk():
                await message.reply("```Sorry, I'm asleep. But I'll read your message ASAP!```")

    async def is_afk(self):
        return False
