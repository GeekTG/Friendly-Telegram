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

from .. import loader, utils

from types import ModuleType

import telethon

logger = logging.getLogger(__name__)

def register(cb):
    cb(RemoteMod())

class RemoteMod(loader.Module):
    """Operate on other accounts"""
    instances = {}
    def __init__(self):
        self.config = {"ACCOUNT_NAME":None}
        self.name = _("Remote Control")
        self.commands = {"remote":self.remote_command}
        self.allmodules = None

    async def client_ready(self, client, db):
        self.instances[client] = self

    async def remote_command(self, message):
        """Execute remote command"""
        # Validation
        args = utils.get_args(message)
        if len(args) < 2:
            await message.edit("<code>What account and operation should be performed?</code>")
            return
        account = args[0].strip()
        command = getattr(self, args[1] + "cmd", None)
        if not callable(command):
            await message.edit("<code>Invalid command</code>")
            return
        account = await self.find_account(account)
        if account is None:
            await message.edit("<code>Invalid account</code>")
            return
        await command(account, args[2:], message)

    async def find_account(self, account):
        # phone, id, username, first name, last name, full name
        clients = []
        for client in self.allclients:
#            if self.instances[client].config["ACCOUNT_NAME"] == account:
#                return client
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
    async def sendcmd(self, client, args, message):
        await client.send_message(args[0], " ".join(args[1:]))

    async def customcmd(self, client, args, message):
        if len(args) < 1:
            await message.edit("<code>What custom client command should be executed?</code>")
            return
        cmd = getattr(client, args[0], None)
        if not callable(cmd):
            await message.edit("<code>That custom client command does not exist!</code>")
            return
        try:
            args = ast.literal_eval(" ".join(args[1:]))
        except ValueError:
            await message.edit("<code>Malformed parameters</code>")
            return
        except SyntaxError:
            args = []
        await cmd(*args)

    async def cmdcmd(self, client, args, message):
        if len(args) < 1:
            await message.edit("<code>What custom client command should be executed?</code>")
            return
        await self.instances[client].allmodules.dispatch(args[0], message)
