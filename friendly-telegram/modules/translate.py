# -*- coding: future_fstrings -*-

import logging
from Yandex import Translate

from .. import loader, utils

logger = logging.getLogger(__name__)

def register(cb):
    cb(TranslateMod())

class TranslateMod(loader.Module):
    """Translator"""
    def __init__(self):
        self.commands = {"translate":self.translatecmd}
        self.config = {"DEFAULT_LANG":"en", "API_KEY":""}
        self.name = "Translator"

    def config_complete(self):
        self.tr = Translate(self.config["API_KEY"])

    async def translatecmd(self, message):
        """.translate [from_lang->][->to_lang] <text>"""
        args = utils.get_args(message)

        if len(args) == 0 or not "->" in args[0]:
            text = " ".join(args)
            args = ["", self.config["DEFAULT_LANG"]]
        else:
            text = " ".join(args[1:])
            args = args[0].split("->")

        if len(text) == 0 and message.is_reply:
            text = await message.get_reply_message().message
        if len(text) == 0:
            await message.edit("Invalid text to translate")
            return



        if args[0] == "":
            args[0] = self.tr.detect(text)
        if len(args) == 3:
            del args[1]
        if len(args) == 1:
            logging.error("python split() error, if there is -> in the text, it must split!")
            raise RuntimeException()
        if args[1] == "":
            args[1] = self.config["DEFAULT_LANG"]
        logger.debug(args)
        translated = self.tr.translate(text, args[1], args[0])
        ret = "<b>Translated </b><code>"
        ret += utils.escape_html(text)
        ret += "</code><b> from </b><code>"
        ret += utils.escape_html(args[0])
        ret += "</code><b> to </b><code>"
        ret += utils.escape_html(args[1])
        ret += "</code><b> and it reads </b><code>"
        ret += utils.escape_html(translated)
        ret += "</code>"
        await message.edit(ret)
