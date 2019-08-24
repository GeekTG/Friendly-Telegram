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

from .. import loader, main, utils


def register(cb):
    cb(CoreMod())


class CoreMod(loader.Module):
    """Control core userbot settings"""
    def __init__(self):
        self.name = _("Settings")

    async def client_ready(self, client, db):
        self._db = db

    async def blacklistcommon(self, message):
        args = utils.get_args(message)
        if len(args) > 1:
            await message.edit(_("<code>Too many args</code>"))
            return
        id = None
        if len(args) == 1:
            try:
                id = int(args[0])
            except ValueError:
                pass
        if id is None:
            id = utils.get_chat_id(message)
        return id

    async def blacklistcmd(self, message):
        """.blacklist [id]
           Blacklist the bot from operating somewhere"""
        id = await self.blacklistcommon(message)
        self._db.set(main.__name__, "blacklist_chats", self._db.get(main.__name__, "blacklist_chats", []) + [id])
        await message.edit(_("<code>Chat {} blacklisted from userbot</code>").format(id))

    async def unblacklistcmd(self, message):
        """.unblacklist [id]
           Unblacklist the bot from operating somewhere"""
        id = await self.blacklistcommon(message)
        self._db.set(main.__name__, "blacklist_chats",
                     list(set(self._db.get(main.__name__, "blacklist_chats", [])) - set([id])))
        await message.edit(_("<code>Chat {} unblacklisted from userbot</code>").format(id))

    async def whitelistcmd(self, message):
        """.whitelist [id]
           Whitelist the bot from operating somewhere"""
        id = await self.blacklistcommon(message)
        self._db.set(main.__name__, "whitelist_chats", self._db.get(main.__name__, "whitelist_chats", []) + [id])
        await message.edit(_("<code>Chat {} whitelisted from userbot</code>").format(id))

    async def unwhitelistcmd(self, message):
        """.unwhitelist [id]
           Unwhitelist the bot from operating somewhere"""
        id = await self.blacklistcommon(message)
        self._db.set(main.__name__, "whitelist_chats",
                     list(set(self._db.get(main.__name__, "whitelist_chats", [])) - set([id])))
        await message.edit(_("<code>Chat {id} unwhitelisted from userbot</code>").format(id))
