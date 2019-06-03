from .. import loader
import logging, random


def register(cb):
    logging.info('Registering %s', __file__)
    cb(YesNoMod())


class YesNoMod(loader.Module):
    """Helps you make important life choices"""
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'yesno': self.yesnocmd}
        self.config = {}
        self.name = "YesNo"

    async def yesnocmd(self, message):
        """Make a life choice"""
        yes = ["Yes", "Yup", "Absolutely", "Non't"]
        no = ["No", "Nope", "Nah", "Yesn't"]
        if random.randint(1, 2) == 1:
            await message.edit(random.choice(yes))
        else:
            await message.edit(random.choice(no))
