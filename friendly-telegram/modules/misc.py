#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .. import loader, utils

import logging
import random

logger = logging.getLogger(__name__)


def register(cb):
    cb(MiscMod())


class MiscMod(loader.Module):
    """Miscellaneous tasks"""
    def __init__(self):
        self.config = {"VOLTE_TEXT": "To be fair, you have to have a very high IQ to understand VoLTE. "
                       + "The technology is extremely subtle, and without a solid grasp of cell towers most "
                       + "of the signal will go over a typical user’s head. There's also Mukesh Ambani’s "
                       + "omniscient outlook, which is deftly woven into his characterisation - his personal "
                       + "philosophy draws heavily from Indian literature, for instance. The users understand "
                       + "this stuff; they have the intellectual capacity to truly appreciate the depths of "
                       + "this technology, to realize that they're not just powerful- they say something deep "
                       + "about LIFE. As a consequence people who dislike reliance jio truly ARE idiots- of "
                       + "course they wouldn't appreciate, for instance, the humour in Mukesh’s existencial "
                       + "catchphrase \"does this roms supports volte????” which itself is a cryptic reference "
                       + "to Turgenev's Russian epic Fathers and Sons I'm smirking right now just imagining one "
                       + "of those addlepated simpletons scratching their heads in confusion as Mukesh Ambani’s "
                       + "genius unfolds itself on their phone screens. What fools... how I pity them. 😂 And yes "
                       + "by the way, I DO have a reliance jio tattoo. And no, you cannot see it. It's for the "
                       + "ladies' eyes only- And even they have to demonstrate that they're phones even supports "
                       + "voltes beforehand.\"", "HUAWEI_TEXT": "Do you even know what a huawei is, i bet you dont, "
                       + "well i made it with one goal, to make a very nice looking ui so i can collect peoples "
                       + "data(nudes) and send them to my indian friends, i bet you are jealous😂😂, and i bet you "
                       + "dont even know how to write a proper OS, well I do, I hired 200 Africian Slaves to work on "
                       + "my new project called HongmengOS, it has 90% better performance than android, and it can "
                       + "even run android apps😍. Infact donald trump almost fucked me in the ass one time, but "
                       + "when I promised to share the \"data\" with him, and send him all the nudes captured from "
                       + "Clinton's CCTV, he let me and my company off the hook, imagine a blonde looking at your "
                       + "dick😂😂, I mean, its not like ive already got yours already, infact I'm working on a "
                       + "new EMUI update to every huawei phone to make it auto-capture every time you jerk off "
                       + "😋, even Tim Cook wants take the hua-way of collecting data, but I bet he doesnt even "
                       + "know how to use AI to capture good nudes. But there is more, I encrypt the nudes on your "
                       + "device so you cant access them, but we can😜, Also take note that I already know your "
                       + "bank details and I'm selling them to tech support scammers, and by the huaway, EMUI 9.2 "
                       + "will have a new A.I in the camera app to enhance dick pics, but you need to agree to "
                       + "the new privacy policy of sharing the nudes you capture to us, for \"product improvement\"",
                       "F_LENGTHS": [5, 1, 1, 4, 1, 1, 1]}
        self.name = _("Miscellaneous")

    async def voltecmd(self, message):
        """Use when the bholit just won't work"""
        await message.edit(self.config["VOLTE_TEXT"])

    async def fcmd(self, message):
        """Pays respects"""
        args = utils.get_args_raw(message)
        if len(args) == 0:
            r = random.randint(0, 3)
            logger.debug(r)
            if r == 0:
                await message.edit("┏━━━┓\n┃┏━━┛\n┃┗━━┓\n┃┏━━┛\n┃┃\n┗┛")
            elif r == 1:
                await message.edit("╭━━━╮\n┃╭━━╯\n┃╰━━╮\n┃╭━━╯\n┃┃\n╰╯")
            else:
                args = "F"
        if len(args) > 0:
            out = ""
            for line in self.config["F_LENGTHS"]:
                c = max(round(line / len(args)), 1)
                out += (args * c) + "\n"
            await message.edit("<code>" + utils.escape_html(out) + "</code>")

    async def huaweicmd(self, message):
        """Use when your country is "investing" in Huawei 5G modems"""
        await message.edit(self.config["HUAWEI_TEXT"])
