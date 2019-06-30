from .. import loader

def register(cb):
    cb(MiscMod())

class MiscMod(loader.Module):
    """Miscellaneous tasks"""
    def __init__(self):
        self.commands = {'volte':self.voltecmd, 'f':self.fcmd}
        self.config = {"VOLTE_TEXT":"To be fair, you have to have a very high IQ to understand VoLTE. The technology is extremely subtle, and without a solid grasp of cell towers most of the signal will go over a typical user’s head. There's also Mukesh Ambani’s omniscient outlook, which is deftly woven into his characterisation - his personal philosophy draws heavily from Indian literature, for instance. The users understand this stuff; they have the intellectual capacity to truly appreciate the depths of this technology, to realize that they're not just powerful- they say something deep about LIFE. As a consequence people who dislike reliance jio truly ARE idiots- of course they wouldn't appreciate, for instance, the humour in Mukesh’s existencial catchphrase \"does this roms supports volte????” which itself is a cryptic reference to Turgenev's Russian epic Fathers and Sons I'm smirking right now just imagining one of those addlepated simpletons scratching their heads in confusion as Mukesh Ambani’s genius unfolds itself on their phone screens. What fools... how I pity them. 😂 And yes by the way, I DO have a reliance jio tattoo. And no, you cannot see it. It's for the ladies' eyes only- And even they have to demonstrate that they're phones even supports voltes beforehand.\""}
        self.name = "Miscellaneous"

    async def voltecmd(self, message):
        await message.edit(self.config["VOLTE_TEXT"])

    async def fcmd(self, message):
        """Pays respects"""
        await message.edit("┏━━━┓\n┃┏━━┛\n┃┗━━┓\n┃┏━━┛\n┃┃\n┗┛")

