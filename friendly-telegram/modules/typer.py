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

from .. import loader, utils
from telethon.errors.rpcerrorlist import *
import logging, time, asyncio

logger = logging.getLogger(__name__)

def register(cb):
    cb(TyperMod())

class TyperMod(loader.Module):
    """Makes your messages type slower"""
    def __init__(self):
        self.config = {"TYPE_CHAR":"▒"}
        self.name = "Typewriter"

    async def typecmd(self, message):
        """.type <message>"""
        a = utils.get_args_raw(message)
        m = ""
        for c in a:
            m += self.config["TYPE_CHAR"]
            message = await update_message(message, m)
            await asyncio.sleep(0.04)
            m = m[:-1]+c
            message = await update_message(message, m)
            await asyncio.sleep(0.02)

async def update_message(message, m):
    try:
        await message.edit(m)
    except MessageNotModifiedError:
        pass # space doesnt count
    except MessageIdInvalidError: # It's gone!
        try:
            logger.warning("message id invalid")
            message.delete()
        except:
            logger.warning("message gone!") # WTF? It's really not here...
        message = await message.client.send_message(message.to_id, m) # Make a new one.
        await asyncio.sleep(10)
    return message
