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
        self.strings = {"name": "Settings",
                        "too_many_args": "<code>Too many args</code>",
                        "blacklisted": "<code>Chat {} blacklisted from userbot</code>",
                        "unblacklisted": "<code>Chat {} unblacklisted from userbot</code>",
                        "what_prefix": "<code>What should the prefix be set to?</code>",
                        "prefix_set": ("<b>Command prefix updated. Type </b><code>{newprefix}setprefix {oldprefix}"
                                       "</code><b> to change it back</b>"),
                        "alias_created": "Alias created. Access it with <code>{}</code>",
                        "no_command": "Command <code>{}</code> does not exist"}

    def config_complete(self):
        self.name = self.strings["name"]

    async def client_ready(self, client, db):
        self._db = db

    async def blacklistcommon(self, message):
        args = utils.get_args(message)
        if len(args) > 1:
            await utils.answer(message, self.strings["too_many_args"])
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
        await utils.answer(message, self.strings["blacklisted"].format(id))

    async def unblacklistcmd(self, message):
        """.unblacklist [id]
           Unblacklist the bot from operating somewhere"""
        id = await self.blacklistcommon(message)
        self._db.set(main.__name__, "blacklist_chats",
                     list(set(self._db.get(main.__name__, "blacklist_chats", [])) - set([id])))
        await utils.answer(message, self.strings["unblacklisted"].format(id))

    async def setprefixcmd(self, message):
        """Sets command prefix"""
        args = utils.get_args(message)
        if len(args) != 1:
            await utils.answer(message, self.strings["what_prefix"])
            return
        oldprefix = self._db.get(main.__name__, "command_prefix", ".")
        self._db.set(main.__name__, "command_prefix", args[0])
        await utils.answer(message, self.strings["prefix_set"].format(newprefix=utils.escape_html(args[0]),
                                                                      oldprefix=utils.escape_html(oldprefix)))

    async def addaliascmd(self, message):
        """Set an alias for a command"""
        args = utils.get_args(message)
        if len(args) != 2:
            return await message.edit(_("You must provide a message and the alias for it"))
        alias, cmd = args
        ret = self.allmodules.add_alias(alias, cmd)
        if ret:
            self._db.set(__name__, "aliases", {**self._db.get(__name__, "aliases"), alias: cmd})
            await utils.answer(message, self.strings["alias_created"].format(utils.escape_html(alias)))
        else:
            await utils.answer(message, self.strings["no_command"].format(utils.escape_html(cmd)))

    async def _client_ready2(self, client, db):
        ret = {}
        for alias, cmd in db.get(__name__, "aliases", {}).items():
            if self.allmodules.add_alias(alias, cmd):
                ret[alias] = cmd
        db.set(__name__, "aliases", ret)
