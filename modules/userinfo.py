from .. import loader, utils
import logging
from telethon.tl.functions.users import GetFullUserRequest


def register(cb):
    logging.info('Registering %s', __file__)
    cb(UserInfoMod())


class UserInfoMod(loader.Module):
    """Tells you about people"""
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'uinfo': self.userinfocmd}
        self.config = {}
        self.name = "User Info"

    async def userinfocmd(self, message):
        """Use in reply to get user info"""
        if message.is_reply:
            full = await message.client(GetFullUserRequest((await message.get_reply_message()).from_id))
        else:
            args = utils.get_args(message)
            full = await message.client(GetFullUserRequest(args[0]))
        logging.debug(full)
        reply = "First name: <code>" + utils.escape_html(full.user.first_name)
        reply += "</code>\nLast name: <code>" + utils.escape_html(str(full.user.last_name))
        reply += "</code>\nBio: <code>" + utils.escape_html(full.about)
        reply += "</code>\nRestricted: <code>" + utils.escape_html(str(full.user.restricted))
        reply += "</code>"
        await message.edit(reply, parse_mode="HTML")
