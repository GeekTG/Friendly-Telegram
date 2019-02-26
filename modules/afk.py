from .. import loader, main
import logging

def register(cb):
    logging.debug('registering %s', __file__)
    cb(AFKMod())

class AFKMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {}
        self.name = "AFK"
        self._me = main.client.get_me()
    async def watcher(self, message):
        print(getattr(message.to_id, 'user_id', None))
        if message.mentioned or getattr(message.to_id, 'user_id', None) == self._me.id:
            logging.debug("tagged!")
            if await self.is_afk():
                await message.reply("```Sorry, I'm busy. But I'll read your message ASAP!```")

    async def is_afk(self):
        return False
