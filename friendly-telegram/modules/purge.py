#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .. import loader
import logging

logger = logging.getLogger(__name__)

def register(cb):
    cb(PurgeMod())

class PurgeMod(loader.Module):
    """Deletes your messages"""
    def __init__(self):
        self.commands = {'purge':self.purgecmd, "del":self.delcmd}
        self.config = {}
        self.name = "Purge"

    async def purgecmd(self, message):
        """Purge from the replied message"""
        if not message.is_reply:
            await message.edit("From where shall I purge?")
            return
        msgs = []
        async for msg in message.client.iter_messages(
                entity=message.to_id,
                min_id=message.reply_to_msg_id,
                reverse=True):
            msgs += [msg.id]
            # No async list comprehension in 3.5
        logger.debug(msgs)
        await message.client.delete_messages(message.to_id, msgs+[message.reply_to_msg_id])

    async def delcmd(self, message):
        """Delete the replied message"""
        msgs = [message.id]
        if not message.is_reply:
            iter = message.client.iter_messages(
                entity=message.to_id
            )
            await iter.__anext__()
            msgs += [(await iter.__anext__()).id]
        else:
            msgs += [(await message.get_reply_message()).id]
        logger.debug(msgs)
        await message.client.delete_messages(message.to_id, msgs)
