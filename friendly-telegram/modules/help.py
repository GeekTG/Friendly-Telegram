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

import inspect
import logging

from telethon.tl.functions.channels import JoinChannelRequest

from .. import loader, utils, main, security

logger = logging.getLogger(__name__)


@loader.tds
class HelpMod(loader.Module):
    """Provides this help message"""

    strings = {
        "name": "Help",
        "bad_module": "🚫 <b>Invalid module name specified</b>",
        "single_mod_header": "ℹ️ <b>Help for</b> <u>{}</u>:",
        "single_cmd": "\n• <code><u>{}</u></code>\n",
        "undoc_cmd": "👁‍🗨 No docs",
        "all_header": "<b>Available GeekTG Modules:</b>",
        "mod_tmpl": "\n• <b>{}</b>",
        "first_cmd_tmpl": ": <code>{}",
        "cmd_tmpl": ", {}",
        "joined": "👩‍💼 <b>Joined to</b> <a href='https://t.me/GeekTGChat'>support chat</a>",
        "join": "👩‍💼 <b>Join the</b> <a href='https://t.me/GeekTGChat'>support chat</a>",
    }

    @loader.unrestricted
    async def helpcmd(self, message):
        """[module] - Get help for module, or get the list of modules"""
        args = utils.get_args_raw(message)

        if args:
            module = None

            for mod in self.allmodules.modules:
                if mod.strings("name", message).lower() == args.lower():
                    module = mod

            if module is None:
                await utils.answer(message, self.strings("bad_module", message))
                return

            try:
                name = module.strings["name"]
            except KeyError:
                name = "Unspecified Name"
            reply = self.strings("single_mod_header", message).format(
                utils.escape_html(name)
            )

            if module.__doc__:
                reply += "\n" + "\n".join(
                    f"  {t}"
                    for t in utils.escape_html(inspect.getdoc(module)).split("\n")
                )

            else:
                logger.warning("Module %s is missing docstring!", module)

            commands = {
                name: func
                for name, func in module.commands.items()
                if await self.allmodules.check_security(message, func)
            }

            for name, fun in commands.items():
                reply += self.strings("single_cmd", message).format(name)

                if fun.__doc__:
                    reply += utils.escape_html(
                        "\n".join(f"  {t}" for t in inspect.getdoc(fun).split("\n"))
                    )
                else:
                    reply += self.strings("undoc_cmd", message)
        else:
            reply = self.strings("all_header", message).format(
                utils.escape_html(
                    (self.db.get(main.__name__, "command_prefix", False) or ".")[0]
                )
            )  # noqa

            for mod in self.allmodules.modules:
                try:
                    name = mod.strings("name", message)
                except KeyError:
                    name = getattr(mod, "name", "ERROR")

                if name not in [
                    "Logger",
                    "Raphielgang Configuration Placeholder",
                    "Uniborg configuration placeholder",
                ]:
                    reply += self.strings("mod_tmpl", message).format(name)
                    first = True
                    try:
                        commands = [
                            name
                            for name, func in mod.commands.items()
                            if await self.allmodules.check_security(message, func)
                        ]
                        for cmd in commands:
                            if first:
                                reply += self.strings("first_cmd_tmpl", message).format(
                                    cmd
                                )
                                first = False
                            else:
                                reply += self.strings("cmd_tmpl", message).format(cmd)
                        reply += "</code>"
                    except Exception:
                        # TODO: FIX THAT SHIT
                        pass

        await utils.answer(message, reply)

    @loader.unrestricted
    async def supportcmd(self, message):
        """Joins the support GeekTG chat"""
        if await self.allmodules.check_security(
            message, security.OWNER | security.SUDO
        ):
            await self.client(JoinChannelRequest("https://t.me/GeekTGChat"))

            try:
                await self.inline.form(
                    self.strings("joined", message),
                    reply_markup=[
                        [{"text": "👩‍💼 Chat", "url": "https://t.me/GeekTGChat"}]
                    ],
                    ttl=10,
                    message=message,
                )
            except Exception:
                await utils.answer(message, self.strings("joined", message))
        else:
            try:
                await self.inline.form(
                    self.strings("join", message),
                    reply_markup=[
                        [{"text": "👩‍💼 Chat", "url": "https://t.me/GeekTGChat"}]
                    ],
                    ttl=10,
                    message=message,
                )
            except Exception:
                await utils.answer(message, self.strings("join", message))

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
