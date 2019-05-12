from .. import loader, utils, main
import logging
from telethon.tl.functions.users import GetFullUserRequest


def register(cb):
    logging.info('Registering %s', __file__)
    cb(BioMod())


class BioMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'bio': self.biocmd}
        self.config = {}
        self.name = "BioMod"

    async def biocmd(self, message):
        args = utils.get_args(message)
        full = await main.client(GetFullUserRequest(args[0]))
        bio = full.about
        await message.edit(bio)