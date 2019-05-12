from .. import loader
import logging
import random


def register(cb):
    logging.info('Registering %s', __file__)
    cb(YesNoMod())


class YesNoMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'yesno': self.yesnocmd}
        self.config = {}
        self.name = "YesNoMod"

    async def yesnocmd(self, message):
        if random.randint(1, 2) == 1:
                x = random.randint(1, 4)
                if x == 1:
                    await message.edit("Yes")
                elif x == 2:
                    await message.edit("Yup")
                elif x == 3:
                    await message.edit("Absolutely")
                else:
                    await message.edit("Non't")
        else:
            x = random.randint(1, 4)
            if x == 1:
                await message.edit("No")
            elif x == 2:
                await message.edit("Nope")
            elif x == 3:
                await message.edit("Nah")
            else:
                await message.edit("Yesn't")
