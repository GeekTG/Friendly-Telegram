from .. import loader, utils
import logging, random

logger = logging.getLogger(__name__)

def register(cb):
    cb(BEmojiMod())

class BEmojiMod(loader.Module):
    """🅱️-ifies things"""
    def __init__(self):
        self.commands = {'b':self.bcmd}
        self.config = {}
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
            if n % 2 == random.randint(0, 1):
                text[n] = "🅱️"
            else:
                text[n] = c
            n += 1
        text = "".join(text)
        logger.debug(text)
        await utils.answer(message, text)

