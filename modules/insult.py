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
        adjectives_start = ["salty", "fat", "fucking", "shitty", "stupid", "retarded"]
        adjectives_mid = ["little", None]
        nouns = ["cunt", "pig", "pedophile", "alpha male", "retard", "ass licker"]
        starts = ["You're a", "You"]
        ends = ["!!!!", "!", ""]
        start = random.choice(starts)
        adjective_start = random.choice(adjectives_start)
        adjective_mid = random.choice(adjectives_mid)
        noun = random.choice(noun)
        end = random.choice(ends)
        insult = start + " " + adjective_start + " " + adjective_mid + (" " if adjective_mid else "") + noun + end
        await message.edit(insult)

