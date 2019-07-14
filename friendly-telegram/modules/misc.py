from .. import loader

def register(cb):
    cb(MiscMod())

class MiscMod(loader.Module):
    """Miscellaneous tasks"""
    def __init__(self):
        self.commands = {'volte':self.voltecmd, 'f':self.fcmd, 'huawei':self.hwcmd}
        self.config = {"VOLTE_TEXT":"To be fair, you have to have a very high IQ to understand VoLTE. The technology is extremely subtle, and without a solid grasp of cell towers most of the signal will go over a typical user’s head. There's also Mukesh Ambani’s omniscient outlook, which is deftly woven into his characterisation - his personal philosophy draws heavily from Indian literature, for instance. The users understand this stuff; they have the intellectual capacity to truly appreciate the depths of this technology, to realize that they're not just powerful- they say something deep about LIFE. As a consequence people who dislike reliance jio truly ARE idiots- of course they wouldn't appreciate, for instance, the humour in Mukesh’s existencial catchphrase \"does this roms supports volte????” which itself is a cryptic reference to Turgenev's Russian epic Fathers and Sons I'm smirking right now just imagining one of those addlepated simpletons scratching their heads in confusion as Mukesh Ambani’s genius unfolds itself on their phone screens. What fools... how I pity them. 😂 And yes by the way, I DO have a reliance jio tattoo. And no, you cannot see it. It's for the ladies' eyes only- And even they have to demonstrate that they're phones even supports voltes beforehand.\"", "HUAWEI_TEXT": "Do you even know what a huawei is, i bet you dont, well i made it with one goal, to make a very nice looking ui so i can collect peoples data(nudes) and send them to my indian friends, i bet you are jealous😂😂, and i bet you dont even know how to write a proper OS, well I do, I hired 200 Africian Slaves to work on my new project called HongmengOS, it has 90% better performance than android, and it can even run android apps😍. Infact donald trump almost fucked me in the ass one time, but when I promised to share the "data" with him, and send him all the nudes captured from Clinton's CCTV, he let me and my company off the hook, imagine a blonde looking at your dick😂😂, I mean, its not like ive already got yours already, infact I'm working on a new EMUI update to every huawei phone to make it auto-capture every time you jerk off 😋, even Tim Cook wants take the hua-way of collecting data, but I bet he doesnt even know how to use AI to capture good nudes. But there is more, I encrypt the nudes on your device so you cant access them, but we can😜, Also take note that I already know your bank details and I'm selling them to tech support scammers, and by the huaway, EMUI 9.2 will have a new A.I in the camera app to enhance dick pics, but you need to agree to the new privacy policy of sharing the nudes you capture to us, for "product improvement""}
        self.name = "Miscellaneous"

    async def voltecmd(self, message):
        """Use when the bholit just won't work"""
        await message.edit(self.config["VOLTE_TEXT"])

    async def fcmd(self, message):
        """Pays respects"""
        await message.edit("┏━━━┓\n┃┏━━┛\n┃┗━━┓\n┃┏━━┛\n┃┃\n┗┛")

    async def hwcmd(self, message):
        """Use when your country is "investing" in Huawei 5G modems"""
        await message.edit(self.config["HUAWEI_TEXT"])
