# -*- coding: future_fstrings -*-

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

import logging
from Yandex import Translate

from .. import loader, utils

logger = logging.getLogger(__name__)


def register(cb):
    cb(TranslateMod())


class TranslateMod(loader.Module):
    """Translator"""
    def __init__(self):
        self.commands = {"translate": self.translatecmd}
        self.config = {"DEFAULT_LANG": "en", "API_KEY": ""}
        self.name = _("Translator")

    def config_complete(self):
        self.tr = Translate(self.config["API_KEY"])

    async def translatecmd(self, message):
        """.translate [from_lang->][->to_lang] <text>"""
        args = utils.get_args(message)

        if len(args) == 0 or "->" not in args[0]:
            text = " ".join(args)
            args = ["", self.config["DEFAULT_LANG"]]
        else:
            text = " ".join(args[1:])
            args = args[0].split("->")

        if len(text) == 0 and message.is_reply:
            text = (await message.get_reply_message()).message
        if len(text) == 0:
            await message.edit(_("Invalid text to translate"))
            return
        if args[0] == "":
            args[0] = self.tr.detect(text)
        if len(args) == 3:
            del args[1]
        if len(args) == 1:
            logging.error("python split() error, if there is -> in the text, it must split!")
            raise RuntimeError()
        if args[1] == "":
            args[1] = self.config["DEFAULT_LANG"]
        args[0] = args[0].lower()
        logger.debug(args)
        translated = self.tr.translate(text, args[1], args[0])
        ret = _("<b>Translated </b><code>{text}</code><b> from </b><code>{frlang}</code><b> to </b>"
                + "<code>{to}</code><b> and it reads </b><code>{output}</code>")
        ret = ret.format(text=utils.escape_html(text), frlang=utils.escape_html(args[0]),
                         to=utils.escape_html(args[1]), output=utils.escape_html(translated))
        await message.edit(ret)
