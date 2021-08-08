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

#   Code from @govnocodules

import builtins
import itertools
import logging
import sys
import traceback
import types

import telethon
from meval import meval

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class PythonMod(loader.Module):
	"""Python stuff"""
	strings = {"name": "Python",
	           "evaluated": "<b>Executed expression:</b>\n<code>{}</code>\n<b>Returned:</b>\n<code>{}</code>",
	           "evaluate_fail": ("<b>[eval] Failed to execute the expression:</b>\n<code>{}</code>"
	                             "\n\n<b>Error:</b>\n<code>{}</code>"),
	           "execute_fail": ("<b>[exec] Failed to execute the expression:</b>\n<code>{}</code>"
	                            "\n\n<b>Error:</b>\n<code>{}</code>"),
	           "pl_fail": ("<b>[pl] Failed to execute the expression:</b>\n<code>{}</code>"
	                       "\n\n<b>Error:</b>\n<code>{}</code>"),
	           "no_args": "<strong>Invalid arguments</strong>",
	           "not_found": "<strong>Command not found</strong>"}

	exceptions = ["code", "globs", "kwargs"]

	async def client_ready(self, client, db):
		self.client = client
		self.db = db

	class FakeCommand:
		def __init__(self, message, name, command):
			self.context = message
			self.name = name
			self.command = command

		async def __call__(self, *args):
			msg = "." + self.name + " " + " ".join(map(str, args))
			reply = await self.context.get_reply_message()
			event = await reply.reply(msg) if reply else await self.context.respond(msg)
			await self.command(event)

	@loader.owner
	async def plcmd(self, message):
		"""pl [code]
		await any_ftg_command(args: str)"""
		arg = utils.get_args_raw(message)

		env = {"message": message, "_": builtins}
		for name, cmd in self.allmodules.commands.items():
			if name in self.exceptions:
				name = "_" + name
			env[name] = self.FakeCommand(message, name, cmd)

		for name, source in self.allmodules.aliases.items():
			if name in self.exceptions:
				name = "_" + name
			env[name] = self.FakeCommand(message, name, self.allmodules.commands[source])

		env.update(await self.getattrs(message))

		try:
			await meval(arg, globals(), **env)

		except Exception:
			phone = message.client.phone
			exc = sys.exc_info()
			exc = "".join(traceback.format_exception(exc[0], exc[1], exc[2].tb_next.tb_next.tb_next))
			exc = exc.replace(str(phone), "❚" * len(str(phone)))
			await utils.answer(message, self.strings("pl_fail", message)
			                   .format(utils.escape_html(utils.get_args_raw(message)), utils.escape_html(exc)))

	@loader.owner
	async def excmd(self, message):
		"""ex [count] [command] [args...]
		execute ftg `command` `count` times with `args`"""
		args = message.raw_text.split(" ", maxsplit=3)

		if len(args) < 3:
			await utils.answer(message, self.strings("no_args", message))
			return

		if args[2] in self.allmodules.aliases.keys():
			command = self.allmodules.commands[self.allmodules.aliases[args[2]]]
		elif args[2] in self.allmodules.commands.keys():
			command = self.allmodules.commands[args[2]]
		else:
			await utils.answer(message, self.strings("not_found", message))
			return
		await message.delete()
		reply = await message.get_reply_message()
		for i in range(int(args[1])):
			msg = "." + " ".join(args[2:]).format(n=i)
			event = await reply.reply(msg) if reply else await message.respond(msg)
			await command(event)

	@loader.owner
	async def printcmd(self, message):
		"""sends args to chat as message"""
		args = utils.get_args_raw(message)
		if not args:
			return await utils.answer(message, self.strings("no_args", message))
		await utils.answer(message, args)

	@loader.owner
	async def evalcmd(self, message):
		""".eval <expression>
		Evaluates python code"""
		phone = message.client.phone
		ret = self.strings("evaluated", message)
		try:
			it = await meval(utils.get_args_raw(message), globals(), **await self.getattrs(message))
		except Exception:
			exc = sys.exc_info()
			exc = "".join(traceback.format_exception(exc[0], exc[1], exc[2].tb_next.tb_next.tb_next))
			exc = exc.replace(phone, "❚" * len(phone))
			await utils.answer(message, self.strings("evaluate_fail", message)
			                   .format(utils.escape_html(utils.get_args_raw(message)), utils.escape_html(exc)))
			return
		ret = ret.format(utils.escape_html(utils.get_args_raw(message)), utils.escape_html(it))
		ret = ret.replace(str(phone), "❚" * len(str(phone)))
		await utils.answer(message, ret)

	@loader.owner
	async def execcmd(self, message):
		""".exec <expression>
		Executes python code"""
		phone = message.client.phone
		try:
			await meval(utils.get_args_raw(message), globals(), **await self.getattrs(message))
		except Exception:
			exc = sys.exc_info()
			exc = "".join(traceback.format_exception(exc[0], exc[1], exc[2].tb_next.tb_next.tb_next))
			exc = exc.replace(str(phone), "❚" * len(str(phone)))
			await utils.answer(message, self.strings("execute_fail", message)
			                   .format(utils.escape_html(utils.get_args_raw(message)), utils.escape_html(exc)))

	async def getattrs(self, message):
		return {"message": message, "client": self.client, "self": self, "db": self.db,
		        "reply": await message.get_reply_message(), **self.get_types(), **self.get_functions(),
		        "event": message, "chat": message.to_id}

	def get_types(self):
		return self.get_sub(telethon.tl.types)

	def get_functions(self):
		return self.get_sub(telethon.tl.functions)

	def get_sub(self, it, _depth=1):
		"""Get all callable capitalised objects in an object recursively, ignoring _*"""
		# TODO: refactor
		return {**dict(filter(lambda x: x[0][0] != "_" and x[0][0].upper() == x[0][0] and callable(x[1]),
		                      it.__dict__.items())),
		        **dict(itertools.chain.from_iterable([self.get_sub(y[1], _depth + 1).items() for y in
		                                              filter(lambda x: x[0][0] != "_"
		                                                               and isinstance(x[1], types.ModuleType)
		                                                               and x[1] != it
		                                                               and x[1].__package__.rsplit(".", _depth)[0]
		                                                               == "telethon.tl",
		                                                     it.__dict__.items())]))}
