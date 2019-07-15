from .. import loader, utils
import logging
from telethon.tl.functions.users import GetFullUserRequest

logger = logging.getLogger(__name__)

def register(cb):
    cb(UserInfoMod())


class UserInfoMod(loader.Module):
    """Tells you about people"""
    def __init__(self):
        self.commands = {'uinfo': self.userinfocmd, "permalink":self.getusercmd}
        self.config = {}
        self.name = "User Info"

    async def userinfocmd(self, message):
        """Use in reply to get user info"""
        if message.is_reply:
            full = await message.client(GetFullUserRequest((await message.get_reply_message()).from_id))
        else:
            args = utils.get_args(message)
            full = await message.client(GetFullUserRequest(args[0]))
        logger.debug(full)
        reply = "First name: <code>" + utils.escape_html(full.user.first_name)
        reply += "</code>\nLast name: <code>" + utils.escape_html(str(full.user.last_name))
        reply += "</code>\nBio: <code>" + utils.escape_html(full.about)
        reply += "</code>\nRestricted: <code>" + utils.escape_html(str(full.user.restricted))
        reply += "</code>"
        await message.edit(reply)

    async def getusercmd(self, message):
        """Get permalink to user based on ID or username"""
        args = utils.get_args(message)
        if len(args) != 1:
            await message.edit("Provide a user to locate")
            return
        try:
            user = int(args[0])
        except ValueError:
            user = args[0]
        try:
            user = await message.client.get_input_entity(user)
        except ValueError:
            # look for the user
            await message.edit("Searching for user...")
            await message.client.get_dialogs()
            try:
                user = await message.client.get_input_entity(user)
            except ValueError:
                # look harder for the user
                await message.edit("Searching harder for user... May take several minutes, or even hours.")
                # Todo look in every group the user is in, in batches. After each batch, attempt to get the input entity again
                try:
                    user = await message.client.get_input_entity(user)
                except:
                    await message.edit("Unable to get permalink!")
                    return
        await message.edit("<a href='tg://user?id={user.id}'>Permalink to {user.id}</a>")
