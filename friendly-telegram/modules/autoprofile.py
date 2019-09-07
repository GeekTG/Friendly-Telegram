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

import asyncio
import time
import logging
from telethon.tl import functions
from .. import loader, utils

logger = logging.getLogger(__name__)


def register(cb):
    cb(AutoProfileMod())


class AutoProfileMod(loader.Module):
    """Automatic stuff for your profile :P"""
    def __init__(self):
        self.name = _("Automatic Profile")
        self.bio_enabled = False
        self.name_enabled = False
        self.raw_bio = None
        self.raw_name = None

    async def client_ready(self, client, db):
        self.client = client

    async def autobiocmd(self, message):
        """ Automatically changes your Telegram's bio with current time, usage:
            .autobio <timeout, seconds> '<message, time as {time}>'"""

        msg = utils.get_args(message)
        if len(msg) != 2:
            return await message.edit(_("<b>AutoBio requires two args.</b>"))
        else:
            raw_bio = msg[1]
            try:
                timeout_autobio = int(msg[0])
            except ValueError as e:
                logger.warning(str(e))
                return await message.edit(_("<b> Wrong time.</b>"))
        if '{time}' not in raw_bio:
            return await message.edit(_("<b>You haven't specified time position/Wrong format.</b>"))

        self.bio_enabled = True
        self.raw_bio = raw_bio
        await message.edit("<b>Successfully enabled autobio.</b>")

        while self.bio_enabled is True:
            current_time = time.strftime("%H:%M")
            bio = raw_bio.format(time=current_time)
            await self.client(functions.account.UpdateProfileRequest(
                about=bio
            ))
            await asyncio.sleep(timeout_autobio)

    async def stopautobiocmd(self, message):
        """ Stop autobio cmd."""

        if self.bio_enabled is False:
            return await message.edit(_("<b>Autobio is already disabled.</b>"))
        else:
            self.bio_enabled = False
            await message.edit(_("<b>Successfully disabled autobio, setting bio to without time.</b>"))
            await self.client(functions.account.UpdateProfileRequest(
                about=self.raw_bio.format(time="")
            ))

    async def autonamecmd(self, message):
        """ Automatically changes your Telegram name with current time, usage:
            .autoname <timeout, seconds> '<message, time as {time}>'"""

        msg = utils.get_args(message)
        if len(msg) != 2:
            return await message.edit(_("<b>AutoName requires two args.</b>"))
        else:
            raw_name = msg[1]
            try:
                timeout_autoname = int(msg[0])
            except ValueError as e:
                logger.error(str(e))
                return await message.edit(_("<b>Wrong time.</b>"))
        if "{time}" not in raw_name:
            return await message.edit(_("<b>You haven't specified time position/Wrong format.</b>"))

        self.name_enabled = True
        self.raw_name = raw_name
        await message.edit(_("<b>Successfully enabled autoname.</b>"))

        while self.name_enabled is True:
            current_time = time.strftime("%H:%M")
            name = raw_name.format(time=current_time)
            await self.client(functions.account.UpdateProfileRequest(
                first_name=name
            ))
            await asyncio.sleep(timeout_autoname)

    async def stopautonamecmd(self, message):
        """ Stop autoname cmd."""

        if self.name_enabled is False:
            return await message.edit(_("<b>Autoname is already disabled.</b>"))
        else:
            self.name_enabled = False
            await message.edit(_("<b>Successfully disabled autoname, setting name to without time.</b>"))
            await self.client(functions.account.UpdateProfileRequest(
                first_name=self.raw_name.format(time="")
            ))
