from .. import loader, utils
import logging, random
from pyfiglet import Figlet, FontNotFound

logger = logging.getLogger(__name__)

def register(cb):
    cb(MockMod())

class MockMod(loader.Module):
    """mOcKs PeOpLe"""
    def __init__(self):
        self.commands = {'mock':self.mockcmd, "figlet":self.figcmd}
        self.config = {}
        self.name = "Mocker"

    async def mockcmd(self, message):
        """Use in reply to another message or as .mock <text>"""
        if message.is_reply:
            text = (await message.get_reply_message()).message
        else:
            text = utils.get_args_raw(message.message)
        if text is None:
            await message.edit("rEpLy To A mEsSaGe To MoCk It (Or TyPe ThE mEsSaGe AfTeR tHe CoMmAnD)")
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

    async def figcmd(self, message):
        """.figlet <font> <text>"""
        args = utils.get_args(message)
        text = " ".join(args[1:])
        mode = args[0]
        fig = Figlet(font=mode)
        try:
            await message.edit("<code>"+utils.escape_html(fig.renderText(text))+"</code>")
        except FontNotFound:
            await message.edit("<code>Font not found</code>")
