from .. import loader
import logging
import random

def register(cb):
    logging.debug('Registering %s', __file__)
    cb(InsultMod())


class InsultMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'insult':self.insultcmd}
        self.config = {}
        self.name = "InsultMod"

    async def insultcmd(self, message):
        adjectives = ["salty ", "fat ", "fucking ", "shitty ", "stupid ", "retarded"]
        verbs = ["cunt ", "pig ", "pedophile ", "alpha male ", "retard", "ass licker "]
        insult = "You're a " + random.choice(adjectives) + random.choice(verbs)
        await message.edit(insult)

