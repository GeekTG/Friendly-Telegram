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
import logging, random

logger = logging.getLogger(__name__)

def register(cb):
    cb(BEmojiMod())

class BEmojiMod(loader.Module):
    """🅱️-ifies things"""
    def __init__(self):
        self.commands = {'b':self.bcmd}
        self.config = {"REPLACABLE_CHARS": "bdfgpv"}
        self.name = "🅱️"

    async def bcmd(self, message):
        """Use in reply to another message or as .b <text>"""
        if message.is_reply:
            text = (await message.get_reply_message()).message
        else:
            text = utils.get_args_raw(message.message)
        if text is None:
            await message.edit("There's nothing to 🅱️-ify")
            return
        text = list(text)
        n = 0
        for c in text:
            if c.lower() == c.upper():
                n += 1
                continue
            if len(self.config["REPLACABLE_CHARS"]) == 0:
                if n % 2 == random.randint(0, 1):
                    text[n] = "🅱️"
                else:
                    text[n] = c
            else:
                if c.lower() in self.config["REPLACABLE_CHARS"]:
                    text[n] = "🅱️"
                else:
                    text[n] = c
            n += 1
        text = "".join(text)
        logger.debug(text)
        await utils.answer(message, text)

