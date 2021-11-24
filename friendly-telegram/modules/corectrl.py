#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2021 The Authors

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

#    Modded by GeekTG Team

import os

import telethon

from .. import loader, main, utils


@loader.tds
class CoreMod(loader.Module):
    """Control core userbot settings"""
    strings = {"name": "Settings",
               "too_many_args": "🚫 <b>Too many args</b>",
               "blacklisted": "✅ <b>Chat {} blacklisted from userbot</b>",
               "unblacklisted": "✅ <b>Chat {} unblacklisted from userbot</b>",
               "user_blacklisted": "✅ <b>User {} blacklisted from userbot</b>",
               "user_unblacklisted": "✅ <b>User {} unblacklisted from userbot</b>",
               "what_prefix": "❓ <b>What should the prefix be set to?</b>",
               "prefix_set": ("✅ <b>Command prefix updated. Type</b> <code>{newprefix}setprefix {oldprefix}"
                              "</code> <b>to change it back</b>"),
               "alias_created": "✅ <b>Alias created. Access it with</b> <code>{}</code>",
               "aliases": "<b>Aliases:</b>",
               "no_command": "🚫 <b>Command</b> <code>{}</code> <b>does not exist</b>",
               "alias_args": "🚫 <b>You must provide a command and the alias for it</b>",
               "delalias_args": "🚫 <b>You must provide the alias name</b>",
               "alias_removed": "✅ <b>Alias</b> <code>{}</code> <b>removed.",
               "no_alias": "<b>🚫 Alias</b> <code>{}</code> <b>does not exist</b>",
               "no_pack": "<b>❓ What translation pack should be added?</b>",
               "bad_pack": "<b>✅ Invalid translation pack specified</b>",
               "trnsl_saved": "<b>✅ Translation pack added</b>",
               "packs_cleared": "<b>✅ Translations cleared</b>",
               "lang_set": "<b>✅ Language changed</b>",
               "db_cleared": "<b>✅ Database cleared</b>",
               "no_nickname_on": "<b>👍 Now commands <u>will work</u> without nickname</b>",
               "no_nickname_off": "<b>👍 Now commands <u>won't work</u> without nickname</b>",
               "no_nickname_status": "<b>🎬 Right now commands <u>can{}</u> be run without nickname</b>",
               "nn_args": "🚫<b> Usage: .nonick [on/off]</b>"}

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    async def blacklistcommon(self, message):
        args = utils.get_args(message)
        if len(args) > 2:
            await utils.answer(message, self.strings("too_many_args", message))
            return
        chatid = None
        module = None
        if args:
            try:
                chatid = int(args[0])
            except ValueError:
                module = args[0]
        if len(args) == 2:
            module = args[1]
        if chatid is None:
            chatid = utils.get_chat_id(message)
        module = self.allmodules.get_classname(module)
        return str(chatid) + "." + module if module else chatid

    async def blacklistcmd(self, message):
        """.blacklist [id]
        Blacklist the bot from operating somewhere"""
        chatid = await self.blacklistcommon(message)
        self._db.set(main.__name__, "blacklist_chats", self._db.get(main.__name__, "blacklist_chats", []) + [chatid])
        await utils.answer(message, self.strings("blacklisted", message).format(chatid))

    async def unblacklistcmd(self, message):
        """.unblacklist [id]
        Unblacklist the bot from operating somewhere"""
        chatid = await self.blacklistcommon(message)
        self._db.set(main.__name__, "blacklist_chats",
                     list(set(self._db.get(main.__name__, "blacklist_chats", [])) - set([chatid])))
        await utils.answer(message, self.strings("unblacklisted", message).format(chatid))

    async def getuser(self, message):
        try:
            return int(utils.get_args(message)[0])
        except (ValueError, IndexError):
            reply = await message.get_reply_message()
            if reply:
                return (await message.get_reply_message()).sender_id

            if message.is_private:
                return message.to_id.user_id
            await utils.answer(message, self.strings("who_to_unblacklist", message))
            return

    async def blacklistusercmd(self, message):
        """.blacklistuser [id]
        Prevent this user from running any commands"""
        user = await self.getuser(message)
        self._db.set(main.__name__, "blacklist_users", self._db.get(main.__name__, "blacklist_users", []) + [user])
        await utils.answer(message, self.strings("user_blacklisted", message).format(user))

    async def unblacklistusercmd(self, message):
        """.unblacklistuser [id]
        Allow this user to run permitted commands"""
        user = await self.getuser(message)
        self._db.set(main.__name__, "blacklist_users",
                     list(set(self._db.get(main.__name__, "blacklist_users", [])) - set([user])))
        await utils.answer(message, self.strings("user_unblacklisted", message).format(user))

    @loader.owner
    async def nonickcmd(self, message):
        """<on|off> - Toggle No-Nickname mode (performing commands without nickname)"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_nickname_status", message).format("'t" if not self._db.get(main.__name__, "no_nickname", False) else ""))
            return

        if args not in ["on", "off"]:
            await utils.answer(message, self.strings("nn_args", message))
            return

        args = args == "on"
        self._db.set(main.__name__, "no_nickname", args)
        await utils.answer(message, self.strings("no_nickname_on" if args else "no_nickname_off", message))

    @loader.owner
    async def setprefixcmd(self, message):
        """Sets command prefix"""
        args = utils.get_args(message)
        if len(args) == 0:
            await utils.answer(message, self.strings("what_prefix", message))
            return
        oldprefix = self._db.get(main.__name__, "command_prefix", ["."])[0]
        self._db.set(main.__name__, "command_prefix", args)
        await utils.answer(message, self.strings("prefix_set", message).format(newprefix=utils.escape_html(args[0]),
                                                                               oldprefix=utils.escape_html(oldprefix)))

    @loader.owner
    async def aliasescmd(self, message):
        """Print all your aliases"""
        aliases = self.allmodules.aliases
        string = self.strings("aliases", message)
        for i, y in aliases.items():
            string += f"\n{i}: {y}"
        await utils.answer(message, string)

    @loader.owner
    async def addaliascmd(self, message):
        """Set an alias for a command"""
        args = utils.get_args(message)
        if len(args) != 2:
            await utils.answer(message, self.strings("alias_args", message))
            return
        alias, cmd = args
        ret = self.allmodules.add_alias(alias, cmd)
        if ret:
            self._db.set(__name__, "aliases", {**self._db.get(__name__, "aliases"), alias: cmd})
            await utils.answer(message, self.strings("alias_created", message).format(utils.escape_html(alias)))
        else:
            await utils.answer(message, self.strings("no_command", message).format(utils.escape_html(cmd)))

    @loader.owner
    async def delaliascmd(self, message):
        """Remove an alias for a command"""
        args = utils.get_args(message)
        if len(args) != 1:
            await utils.answer(message, self.strings("delalias_args", message))
            return
        alias = args[0]
        ret = self.allmodules.remove_alias(alias)
        if ret:
            current = self._db.get(__name__, "aliases")
            del current[alias]
            self._db.set(__name__, "aliases", current)
            await utils.answer(message, self.strings("alias_removed", message).format(utils.escape_html(alias)))
        else:
            await utils.answer(message, self.strings("no_alias", message).format(utils.escape_html(alias)))

    @loader.owner
    async def aliasescmd(self, message):
        """Print all your aliases"""
        aliases = self.allmodules.aliases
        string = self.strings("aliases", message)
        for i, y in aliases.items():
            string += f"\n{i}: {y}"
        await utils.answer(message, string)

    async def addtrnslcmd(self, message):
        """Add a translation pack
        .addtrnsl <pack>
        Restart required after use"""
        args = utils.get_args(message)
        if len(args) != 1:
            await utils.answer(message, self.strings("no_pack", message))
            return
        pack = args[0]
        if await message.client.is_bot():
            if not pack.isalnum():
                await utils.answer(message, self.strings("bad_pack", message))
                return
            if not os.path.isfile(os.path.join("translations", pack + ".json")):
                await utils.answer(message, self.strings("bad_pack", message))
                return
            self._db.setdefault(main.__name__, {}).setdefault("langpacks", []).append(pack)
            self._db.save()
            await utils.answer(message, self.strings("trnsl_saved", message))
        else:
            try:
                pack = int(pack)
            except ValueError:
                pass
            try:
                pack = await self._client.get_entity(pack)
            except ValueError:
                await utils.answer(message, self.strings("bad_pack", message))
                return
            if isinstance(pack, telethon.tl.types.Channel) and not pack.megagroup:
                self._db.setdefault(main.__name__, {}).setdefault("langpacks", []).append(pack.id)
                self._db.save()
                await utils.answer(message, self.strings("trnsl_saved", message))
            else:
                await utils.answer(message, self.strings("bad_pack", message))

    async def cleartrnslcmd(self, message):
        """Remove all translation packs"""
        self._db.set(main.__name__, "langpacks", [])
        await utils.answer(message, self.strings("packs_cleared", message))

    async def setlangcmd(self, message):
        """Change the preferred language used for translations
        Specify the language as space separated list of ISO 639-1 language codes in order of preference (e.g. fr en)
        With no parameters, all translations are disabled
        Restart required after use"""
        langs = utils.get_args(message)
        self._db.set(main.__name__, "language", langs)
        await utils.answer(message, self.strings("lang_set", message))

    @loader.owner
    async def cleardbcmd(self, message):
        """Clears the entire database, effectively performing a factory reset"""
        self._db.clear()
        await self._db.save()
        await utils.answer(message, self.strings("db_cleared", message))

    async def _client_ready2(self, client, db):
        ret = {
            alias: cmd
            for alias, cmd in db.get(__name__, "aliases", {}).items()
            if self.allmodules.add_alias(alias, cmd)
        }
        db.set(__name__, "aliases", ret)
