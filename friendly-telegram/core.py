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
import os

from . import security, utils, loader

user_modules = None


class TestManager:
	restart = asyncio.Future()

	def __init__(self, client, db, allclients, start_stage):
		self._client = client
		self._db = db
		self._clients = allclients
		self._start_stage = start_stage

	async def init(self):
		stage = self._db.get(__name__, "stage", None)
		if stage is None:
			stage = self._start_stage - 1
			await self._db.set(__name__, "stage", stage)
		if stage > 4:
			stage = 0
			await self._db.set(__name__, "stage", stage)
		if not await self._client.is_bot():
			bot_id = [(await c.get_me(True)).user_id for c in self._clients if c is not self._client][0]
			self._db.set(security.__name__, "bounding_mask", -1)
			if stage == 0:
				self._db.set(security.__name__, "bounding_mask", -1)
				self._db.set(security.__name__, "owner", [bot_id])
				return ["usermodule.py"]
			self._db.set(security.__name__, "owner", [-1])
			if stage == 1:
				self._db.set(security.__name__, "sudo", [bot_id])
				return ["usermodule.py"]
			if stage == 2:
				self._db.set(security.__name__, "sudo", [])
				self._db.set(security.__name__, "support", [bot_id])
				return ["usermodule.py"]
			if stage == 3:
				self._db.set(security.__name__, "support", [])
				return ["usermodule.py"]
			if stage == 4:
				self._db.set(security.__name__, "owner", [bot_id])
				await self._db.set(security.__name__, "bounding_mask", 1)
				defmods = filter(lambda x: (len(x) > 3 and x[-3:] == ".py" and x[0] != "_"),
				                 os.listdir(os.path.join(utils.get_base_dir(), loader.MODULES_NAME)))
				return ["usermodule.py"] + list(defmods)

	def should_restart(self):
		TestManager.restart = asyncio.Future()  # reset
		return self._db.get(__name__, "stage", 0) <= 4
