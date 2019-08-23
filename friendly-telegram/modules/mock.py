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
import logging
import random
from pyfiglet import Figlet, FigletFont, FontNotFound

logger = logging.getLogger(__name__)


def register(cb):
    cb(MockMod())


class MockMod(loader.Module):
    """mOcKs PeOpLe"""
    def __init__(self):
        self.name = _("Mocker")

    async def mockcmd(self, message):
        """Use in reply to another message or as .mock <text>"""
        if message.is_reply:
            text = (await message.get_reply_message()).message
        else:
            text = utils.get_args_raw(message.message)
        if text is None:
            await message.edit(_("rEpLy To A mEsSaGe To MoCk It (Or TyPe ThE mEsSaGe AfTeR tHe CoMmAnD)"))
            return
        text = list(text)
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
        logger.debug(text)
        await message.edit(text)

    async def figletcmd(self, message):
        """.figlet <font> <text>"""
        # We can't localise figlet due to a lack of fonts
        args = utils.get_args(message)
        if len(args) < 2:
            await utils.answer(message, "<code>Supply a font and some text to render with figlet</code>")
            return
        text = " ".join(args[1:])
        mode = args[0]
        if mode == "random":
            mode = random.choice(FigletFont.getFonts())
        try:
            fig = Figlet(font=mode, width=30)
        except FontNotFound:
            await message.edit(_("<code>Font not found</code>"))
            return
        await message.edit("<code>\u206a"+utils.escape_html(fig.renderText(text))+"</code>")
