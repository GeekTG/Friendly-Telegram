from .. import loader
import random

def register(cb):
    cb(YesNoMod())


class YesNoMod(loader.Module):
    """Helps you make important life choices"""
    def __init__(self):
        self.commands = {'yesno': self.yesnocmd}
        self.config = {}
        self.name = "YesNo"

    async def yesnocmd(self, message):
        """Make a life choice"""
        yes = ["Yes", "Yup", "Absolutely", "Non't"]
        no = ["No", "Nope", "Nah", "Yesn't"]
        if random.getrandbits(1):
            await message.edit(random.choice(yes))
        else:
            await message.edit(random.choice(no))
