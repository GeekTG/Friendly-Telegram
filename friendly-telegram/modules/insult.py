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

from .. import loader

import logging
import random


logger = logging.getLogger(__name__)


def register(cb):
    cb(InsultMod())


class InsultMod(loader.Module):
    """Shouts at people"""
    def __init__(self):
        self.name = _("Insulter")

    async def insultcmd(self, message):
        """Use when angry"""
        # TODO localisation?
        adjectives_start = ["salty", "fat", "fucking", "shitty", "stupid", "retarded", "self conscious", "tiny"]
        adjectives_mid = ["little", "vitamin D deficient", "idiotic", "incredibly stupid"]
        nouns = ["cunt", "pig", "pedophile", "beta male", "bottom", "retard", "ass licker", "cunt nugget",
                 "PENIS", "dickhead", "flute", "idiot", "motherfucker", "loner", "creep"]
        starts = ["You're a", "You", "Fuck off you", "Actually die you", "Listen up you",
                  "What the fuck is wrong with you, you"]
        ends = ["!!!!", "!", ""]
        start = random.choice(starts)
        adjective_start = random.choice(adjectives_start)
        adjective_mid = random.choice(adjectives_mid)
        noun = random.choice(nouns)
        end = random.choice(ends)
        insult = start + " " + adjective_start + " " + adjective_mid + (" " if adjective_mid else "") + noun + end
        logger.debug(insult)
        await message.edit(insult)
