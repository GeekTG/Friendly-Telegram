from .. import loader
import logging

def register(cb):
    logging.debug('registering testmod')
    cb(TestMod())

class TestMod(loader.Module):
    def __init__(self):
        logging.debug('testmod started')
        self.commands = {'ping':self.pingcmd}
        self.name = "testmod"
    async def pingcmd(self, message):
        print('pong')
        await message.edit('pong')

