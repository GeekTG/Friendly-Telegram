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

import logging
import inspect

from telethon.tl.functions.channels import JoinChannelRequest

from .. import loader, utils, main

logger = logging.getLogger(__name__)


def register(cb):
    cb(HelpMod())


@loader.tds
class HelpMod(loader.Module):
    """Provides this help message"""
    strings = {"name": "Help",
               "bad_module": "<b>Invalid module name specified</b>",
               "single_mod_header": ("<b>Help for</b> <u>{}</u>:\nNote that the monospace text are the commands "
                                     "and they can be run with <code>{}&lt;command&gt;</code>"),
               "single_cmd": "\n• <code><u>{}</u></code>\n",
               "undoc_cmd": "There is no documentation for this command",
               "all_header": ("<b>Help for</b> <a href='https://t.me/friendlytgbot'>Friendly-Telegram</a>\n"
                              "For more help on how to use a command, type <code>.help &lt;module name&gt;</code>\n\n"
                              "<b>Available Modules:</b>"),
               "mod_tmpl": "\n• <b>{}</b>",
               "first_cmd_tmpl": ": <code>{}",
               "cmd_tmpl": ", {}",
               "footer": ("\n\nYou can <b>read more</b> about most commands "
                          "<a href='https://friendly-telegram.gitlab.io'>here</a>"),
               "joined": "<b>Joined to</b> <a href='https://t.me/friendlytgbot'>support chat</a>"}

    def config_complete(self):
        self.name = self.strings["name"]

    async def helpcmd(self, message):
        """.help [module]"""
        args = utils.get_args_raw(message)
        if args:
            module = None
            for mod in self.allmodules.modules:
                if mod.name.lower() == args.lower():
                    module = mod
            if module is None:
                await utils.answer(message, self.strings["bad_module"])
                return
            # Translate the format specification and the module separately
            reply = self.strings["single_mod_header"].format(utils.escape_html(module.name),
                                                             utils.escape_html(self.db.get(main.__name__,
                                                                                           "command_prefix",
                                                                                           False) or "."))
            if module.__doc__:
                reply += "\n" + "\n".join("  " + t for t in utils.escape_html(inspect.getdoc(module)).split("\n"))
            else:
                logger.warning("Module %s is missing docstring!", module)
            for name, fun in module.commands.items():
                reply += self.strings["single_cmd"].format(name)
                if fun.__doc__:
                    reply += utils.escape_html("\n".join("  " + t for t in inspect.getdoc(fun).split("\n")))
                else:
                    reply += self.strings["undoc_cmd"]
        else:
            reply = self.strings["all_header"]
            for mod in self.allmodules.modules:
                reply += self.strings["mod_tmpl"].format(mod.name)
                first = True
                for cmd in mod.commands:
                    if first:
                        reply += self.strings["first_cmd_tmpl"].format(cmd)
                        first = False
                    else:
                        reply += self.strings["cmd_tmpl"].format(cmd)
                reply += "</code>"
        reply += self.strings["footer"]
        await utils.answer(message, reply)

    async def supportcmd(self, message):
        """Joins the support chat"""
        await self.client(JoinChannelRequest("https://t.me/friendlytgbot"))
        await utils.answer(message, self.strings["joined"])

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
