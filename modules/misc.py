from .. import loader
import logging

def register(cb):
    logging.debug('Registering %s', __file__)
    cb(MiscMod())

class MiscMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'volte':self.voltecmd}
        self.config = {"VOLTE_TEXT":"To be fair, you have to have a very high IQ to understand VoLTE. The technology is extremely subtle, and without a solid grasp of cell towers most of the signal will go over a typical user’s head. There's also Mukesh Ambani’s omniscient outlook, which is deftly woven into his characterisation - his personal philosophy draws heavily from Indian literature, for instance. The users understand this stuff; they have the intellectual capacity to truly appreciate the depths of this technology, to realize that they're not just powerful- they say something deep about LIFE. As a consequence people who dislike reliance jio truly ARE idiots- of course they wouldn't appreciate, for instance, the humour in Mukesh’s existencial catchphrase \"does this roms supports volte????” which itself is a cryptic reference to Turgenev's Russian epic Fathers and Sons I'm smirking right now just imagining one of those addlepated simpletons scratching their heads in confusion as Mukesh Ambani’s genius unfolds itself on their phone screens. What fools... how I pity them. 😂 And yes by the way, I DO have a reliance jio tattoo. And no, you cannot see it. It's for the ladies' eyes only- And even they have to demonstrate that they're phones even supports voltes beforehand.\""}
        self.name = "Miscellaneous"
        self.help = "Mostly shorthand for typing long, fixed texts"

    async def voltecmd(self, message):
        await message.edit(self.config["VOLTE_TEXT"])

