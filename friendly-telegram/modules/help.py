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
import logging, inspect

from telethon.tl.functions.channels import JoinChannelRequest

logger = logging.getLogger(__name__)

def register(cb):
    cb(HelpMod())

class HelpMod(loader.Module):
    """Provides this help message"""
    def __init__(self):
        self.name = "Help"
        self.allmodules = None

    async def helpcmd(self, message):
        """.help [module]"""
        args = utils.get_args_raw(message)
        if args:
            module = None
            for mod in self.allmodules.modules:
                if mod.name.lower() == args.lower():
                    module = mod
            if module is None:
                await message.edit("<code>Invalid module name specified</code>")
                return
            reply = f"<code>Help for {utils.escape_html(module.name)}:\n  "
            if module.__doc__:
                reply += utils.escape_html(inspect.cleandoc(module.__doc__))
            else:
                logger.warning("Module %s is missing docstring!", module)
            for name, fun in module.commands.items():
                reply += f"\n  {name}\n"
                if fun.__doc__:
                    reply += utils.escape_html("\n".join(["    "+x for x in inspect.cleandoc(fun.__doc__).splitlines()]))
                else:
                    reply += "There is no documentation for this command"
        else:
            reply = "<code>Available Modules:\n"
            for mod in self.allmodules.modules:
                reply += f"\n  {utils.escape_html(mod.name)} has {len(mod.commands)} {'command' if len(mod.commands) == 1 else 'commands'} available\n"
                for cmd in mod.commands:
                    reply += f"    {cmd}\n"
        reply += "</code>"
        await message.edit(reply)

    async def supportcmd(self, message):
        """Joins the support chat"""
        await client(JoinChannelRequest("https://t.me/friendlytgbot"))
        await message.edit('<code>Joined to </code><a href="https://t.me/friendlytgbot">support chat</a><code>.</code>')

    async def client_ready(self, client, db):
        self.client = client
