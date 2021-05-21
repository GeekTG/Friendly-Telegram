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

import asyncio
import logging

from . import core
from . import loader, utils

logger = logging.getLogger(__name__)


@loader.test(stages=range(1, 5))
async def ownertest(stage, conv):
	if stage <= 1:
		return "Success"
	else:
		return asyncio.TimeoutError


@loader.test(stages=range(1, 5))
async def sudotest(stage, conv):
	if stage <= 2:
		return "Success"
	else:
		return asyncio.TimeoutError


@loader.test(stages=range(1, 5))
async def supporttest(stage, conv):
	if stage <= 3:
		return "Success"
	else:
		return asyncio.TimeoutError


@loader.test(stages=range(1, 5))
async def admintest(stage, conv):
	if stage <= 2:
		return "Success"
	else:
		return asyncio.TimeoutError


@loader.test(stages=range(1, 5))
async def membertest(stage, conv):
	if stage <= 2:
		return "Success"
	else:
		return asyncio.TimeoutError


@loader.tds
class UserTestMod(loader.Module):
	"""Testing coordinator (user half)"""
	strings = {"name": "Test Coordinator (user)"}

	async def _client_ready2(self, client, db):
		core.user_modules = self.allmodules
		stage = db.get(core.__name__, "stage", 0) + 1
		await db.set(core.__name__, "stage", stage)
		if db.get(__name__, "bot_username", None) is None:
			bot = [(await c.get_me()).username for c in self.allclients if c is not client][0]
			await db.set(__name__, "bot_username", bot)
			self._bot = await client.get_input_entity(bot)
		self._bot = [(await c.get_me(True)).user_id for c in self.allclients if c is not client][0]
		self._client = client
		self._db = db
		asyncio.ensure_future(self.send())

	async def send(self):
		await asyncio.sleep(1)
		await self._client.send_message(self._bot,
		                                "/start@{} stage {}".format(self._db.get(__name__, "bot_username", ""),
		                                                            self._db.get(core.__name__, "stage", 0)))

	@loader.owner
	@loader.test(func=ownertest)
	async def _ownercmd(self, message):
		"""Test"""
		await utils.answer(message, "Success")

	@loader.sudo
	@loader.test(func=sudotest)
	async def _sudocmd(self, message):
		"""Test"""
		await utils.answer(message, "Success")

	@loader.support
	@loader.test(func=supporttest)
	async def _supportcmd(self, message):
		"""Test"""
		await utils.answer(message, "Success")

	@loader.group_admin
	@loader.test(func=admintest)
	async def _admincmd(self, message):
		"""Test"""
		await utils.answer(message, "Success")

	@loader.group_member
	@loader.test(func=membertest)
	async def _membercmd(self, message):
		"""Test"""
		await utils.answer(message, "Success")

	@loader.pm
	@loader.test(resp="Success", stages=range(1, 5))
	async def _pmcmd(self, message):
		"""Test"""
		await utils.answer(message, "Success")

	@loader.unrestricted
	@loader.test(resp="Success", stages=range(1, 5))
	async def _unrestrictedcmd(self, message):
		"""Test"""
		await utils.answer(message, "Success")
