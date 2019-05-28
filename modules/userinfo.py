from .. import loader, utils
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
        self.name = "User Info"
        self.help = "Tells you about people"

    async def userinfocmd(self, message):
        if message.is_reply:
            full = await message.client(GetFullUserRequest((await message.get_reply_message()).from_id))
        else:
            args = utils.get_args(message)
            full = await message.client(GetFullUserRequest(args[0]))
        logging.debug(full)
        reply = "<code>First name: " + full.user.first_name
        reply += "\nLast name: " + str(full.user.last_name)
        reply += "\nBio: " + full.about
        reply += "\nRestricted: " + str(full.user.restricted) + "</code>"
        await message.edit(reply, parse_mode="HTML")
