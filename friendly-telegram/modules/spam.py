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
import asyncio


logger = logging.getLogger(__name__)


def register(cb):
    cb(SpamMod())


class SpamMod(loader.Module):
    """Annoys people really effectively"""
    def __init__(self):
        self.name = _("Spammer")

    async def spamcmd(self, message):
        """.spam <count> <message>"""
        use_reply = False
        args = utils.get_args(message)
        logger.debug(args)
        if len(args) == 0:
            await message.edit(_("U wot? I need something to spam"))
            return
        if len(args) == 1:
            if message.is_reply:
                use_reply = True
            else:
                await message.edit(_("Go spam urself m8"))
                return
        count = args[0]
        spam = (await message.get_reply_message()) if use_reply else message
        spam.message = ' '.join(args[1:])
        try:
            count = int(count)
        except ValueError:
            await message.edit(_("Nice number bro"))
            return
        if count < 1:
            await message.edit(_("Haha much spam"))
            return
        await message.delete()
        if count > 20:
            # Be kind to other people
            sleepy = 2
        else:
            sleepy = 0
        i = 0
        size = 1 if sleepy else 100
        while i < count:
            await asyncio.gather(*[message.respond(spam) for x in range(min(count, size))])
            await asyncio.sleep(sleepy)
            i += size
