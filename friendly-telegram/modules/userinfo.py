# -*- coding: future_fstrings -*-

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

from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import Channel, Chat

logger = logging.getLogger(__name__)


def register(cb):
    cb(UserInfoMod())


class UserInfoMod(loader.Module):
    """Tells you about people"""
    def __init__(self):
        self.name = _("User Info")

    async def userinfocmd(self, message):
        """Use in reply to get user info"""
        if message.is_reply:
            full = await self.client(GetFullUserRequest((await message.get_reply_message()).from_id))
        else:
            args = utils.get_args(message)
            full = await self.client(GetFullUserRequest(args[0]))
        logger.debug(full)
        reply = _("First name: <code>{}</code>").format(utils.escape_html(full.user.first_name))
        reply += _("\nLast name: <code>{}</code>").format(utils.escape_html(str(full.user.last_name)))
        reply += _("\nBio: <code>{}</code>").format(utils.escape_html(full.about))
        reply += _("\nRestricted: <code>{}</code>").format(utils.escape_html(str(full.user.restricted)))
        await message.edit(reply)

    async def permalinkcmd(self, message):
        """Get permalink to user based on ID or username"""
        # Recent server changes make this almost useless. Remove to cleanup code? TODO consider this
        args = utils.get_args(message)
        if len(args) != 1:
            await message.edit(_("Provide a user to locate"))
            return
        try:
            user = int(args[0])
        except ValueError:
            user = args[0]
        try:
            user = await self.client.get_input_entity(user)
        except ValueError as e:
            logger.debug(e)
            # look for the user
            await message.edit(_("Searching for user..."))
            dialogs = await self.client.get_dialogs()
            try:
                user = await self.client.get_input_entity(user)
            except ValueError:
                logger.debug(e)
                # look harder for the user
                basemsg = _("Searching harder for user... May take several minutes, or even hours. "
                            + "Current progress: {}/{}")
                await message.edit(basemsg.format(0, len(dialogs)))
                # Look in every group the user is in, in batches. After each batch,
                # attempt to get the input entity again
                ops = []
                c = 0
                fulluser = None
                for dialog in dialogs:
                    if len(ops) >= 50:
                        logger.debug(str(c)+"/"+str(len(dialogs)))
                        c += 1
                        await asyncio.gather(*ops, message.edit(basemsg.format(c, len(dialogs))),
                                             return_exceptions=True)
                        ops = []
                        try:
                            fulluser = await self.client.get_input_entity(user)
                        except ValueError as e:
                            logger.debug(e)
                    # Channels usually fail because we can't list members.
                    if isinstance(dialog.entity, Chat) or isinstance(dialog.entity, Channel):
                        logger.debug(dialog)
                        ops += [self.client.get_participants(dialog.entity, aggressive=True)]

                # Check once more, in case the entity is in the last 50 peers
                if len(ops):
                    await asyncio.gather(*ops, return_exceptions=True)
                    ops = []
                if fulluser is None:
                    try:
                        fulluser = await self.client.get_input_entity(user)
                    except ValueError as e:
                        logger.error(e)

                if fulluser is None:
                    await message.edit(_("Unable to get permalink!"))
                    return
                else:
                    user = fulluser
        await message.edit(_("<a href='tg://user?id={uid}'>Permalink to {uid}</a>").format(uid=user.user_id))

    async def client_ready(self, client, db):
        self.client = client
