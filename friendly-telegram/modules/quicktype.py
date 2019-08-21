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
import logging, asyncio

logger = logging.getLogger(__name__)

def register(cb):
    cb(QuickTypeMod())

class QuickTypeMod(loader.Module):
    """Deletes your message after a timeout"""
    def __init__(self):
        self.name = _("Quick Typer")

    async def quicktypecmd(self, message):
        """.quicktype <timeout> <message>"""
        args = utils.get_args(message)
        logger.debug(args)
        if len(args) == 0:
            await message.edit(_("U wot? I need something to type"))
            return
        if len(args) == 1:
            await message.edit(_("Go type it urself m8"))
            return
        t = args[0]
        mess = ' '.join(args[1:])
        try:
            t = float(t)
        except ValueError:
            await message.edit(_("Nice number bro"))
            return
        await message.edit(mess)
        await asyncio.sleep(t)
        await message.delete()
