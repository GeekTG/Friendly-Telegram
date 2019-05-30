from .. import loader, utils
import logging, random

def register(cb):
    logging.debug('Registering %s', __file__)
    cb(MockMod())

class MockMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'mock':self.mockcmd}
        self.config = {}
        self.name = "Mocker"
        self.help = "mOcKs PeOpLe"

    async def mockcmd(self, message):
        if message.is_reply:
            text = list((await message.get_reply_message()).message)
        else:
            text = list(utils.get_args_raw(message.message))
        n = 0
        rn = 0
        for c in text:
            if n % 2 == random.randint(0, 1):
                text[rn] = c.upper()
            else:
                text[rn] = c.lower()
            if c.lower() != c.upper():
                n += 1
            rn += 1
        text = "".join(text)
        logging.debug(text)
        await message.edit(text)


