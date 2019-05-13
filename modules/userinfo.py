from .. import loader, utils, main
import logging
from telethon.tl.functions.users import GetFullUserRequest


def register(cb):
    logging.info('Registering %s', __file__)
    cb(UserInfoMod())


class UserInfoMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'uinfo': self.userinfocmd}
        self.config = {}
        self.name = "UserInfoMod"

    async def userinfocmd(self, message):
        args = utils.get_args(message)
        full = await main.client(GetFullUserRequest(args[0]))
        logging.debug(full)
        reply = "`First name: " + full.user.first_name
        reply += "\nLast name: " + str(full.user.last_name)
        reply += "\nBio: " + full.about
        reply += "\nVerified: " + str(full.user.verified) + " (You shouldn't worry about this, it isn't important!)"
        reply += "\nRestricted: " + str(full.user.restricted) + "`"
        await message.edit(reply)