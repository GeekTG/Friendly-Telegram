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
import itertools
import ast

import telethon

from .. import loader, utils

tlfuns = dict(filter(lambda mod: mod[1].__module__.startswith("telethon.tl.functions"),
                     itertools.chain.from_iterable([inspect.getmembers(mod[1], inspect.isclass)
                                                    for mod in inspect.getmembers(telethon.tl.functions,
                                                                                  inspect.ismodule)])))

logger = logging.getLogger(__name__)


def register(cb):
    cb(RemoteMod())


@loader.tds
class RemoteMod(loader.Module):
    """Operate on other accounts"""
    strings = {"name": "Remote Control",
               "account_cfg_doc": "What to call this account in .remote commands",
               "what_account": "<b>What account and operation should be performed?</b>",
               "bad_command": "<b>Invalid command</b>",
               "bad_account": "<b>Invalid account</b>",
               "what_client_command": "<b>What custom client command should be executed?</b>",
               "bad_client_command": "<b>That custom client command does not exist!</b>",
               "what_ftg_command": "<b>What command should be executed?</b>",
               "what_raw_command": "<b>What raw MTProto command should be executed?</b>",
               "bad_raw_command": "<b>Invalid MTProto function</b>"}

    def __init__(self):
        self.config = loader.ModuleConfig("ACCOUNT_NAME", None, lambda: self.strings["account_cfg_doc"])

    def config_complete(self):
        self.name = self.strings["name"]

    async def remotecmd(self, message):
        """Execute remote command"""
        # Validation
        args = utils.get_args(message)
        if len(args) < 2:
            await utils.answer(message, self.strings["what_account"])
            return
        account = args[0].strip()
        command = getattr(self, args[1] + "_command", None)
        if not callable(command):
            await utils.answer(message, self.strings["bad_command"])
            return
        account = await self.find_account(account)
        if account is None:
            await utils.answer(message, self.strings["bad_account"])
            return
        await command(account, args[2:], message)

    async def find_account(self, account):
        # phone, id, username, first name, last name, full name
        clients = []
        for client in self.allclients:
            clients += [[client, await client.get_me()]]
        for client, client_me in clients:
            if client_me.phone == account:
                return client
        for client, client_me in clients:
            if str(client_me.id) == account:
                return client
        for client, client_me in clients:
            if client_me.username == account:
                return client
        for client, client_me in clients:
            if client_me.first_name == account:
                return client
        for client, client_me in clients:
            if client_me.last_name and client_me.last_name == account:
                return client

    # Commands
    async def send_command(self, client, args, message):
        await client.send_message(args[0], " ".join(args[1:]))

    async def custom_command(self, client, args, message):
        if len(args) < 1:
            await utils.answer(message, self.strings["what_client_command"])
            return
        cmd = getattr(client, args[0], None)
        if not callable(cmd):
            await utils.answer(message, self.strings["bad_client_command"])
            return
        fargs = []
        for arg in args[1:]:
            try:
                fargs.append(ast.literal_eval(arg))
            except (ValueError, SyntaxError):
                fargs.append(arg)
        logger.debug(fargs)
        await cmd(*fargs)

    async def cmd_command(self, client, args, message):
        if len(args) < 1:
            await utils.answer(message, self.strings["what_ftg_command"])
            return
        for load in self.allloaders:
            if load.client is client:
                break
                # This will always be fulfilled at some point
        logger.debug(args)
        message.message = " ".join(args[1:])
        msg = await message.client.send_message(args[0], message)
        msg.message, func = load.dispatch(msg.message)
        await func(msg)

    async def raw_command(self, client, args, message):
        if len(args) < 1:
            await utils.answer(message, self.strings["what_raw_command"])
            return
        if not args[0] in tlfuns.keys():
            await utils.answer(message, self.strings["bad_raw_command"])
            return
        func = tlfuns[args[0]]
        await client(func())
