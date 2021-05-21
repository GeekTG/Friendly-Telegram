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

import functools

import aiohttp_jinja2
from aiohttp import web
from jinja2.runtime import Undefined

from .. import main, security


def format(msg):
	if isinstance(msg, str):
		return msg
	if isinstance(msg, int):
		return str(msg)
	if isinstance(msg, list):
		return ", ".join(str(p) for p in msg)
	return ""


class Web:
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.app.router.add_get("/settings", self.settings)
		self.app.router.add_put("/setGroup", self.set_group)
		self.app.router.add_patch("/setPermissionSet", self.set_permission_set)

	@aiohttp_jinja2.template("settings.jinja2")
	async def settings(self, request):
		uid = await self.check_user(request)
		if uid is None:
			return web.Response(status=302, headers={"Location": "/"})  # They gotta sign in.
		keys = [(main.__name__, "prefixes", ["."]),
		        (security.__name__, "owner", None),
		        (security.__name__, "sudo", []),
		        (security.__name__, "support", [])]
		db = self.client_data[uid][2]
		return {"checked": functools.partial(self.is_checked, db), "modules": self.client_data[uid][0].modules,
		        "name": lambda x: x.__name__ if x else "", **security.BITMAP,
		        **{key: format(self.client_data[uid][2].get(mod, key, default)) for mod, key, default in keys}}

	def is_checked(self, db, bit, func, func_name):
		if isinstance(func, Undefined):
			ret = db.get(security.__name__, "bounding_mask", security.DEFAULT_PERMISSIONS) & bit
		else:
			ret = db.get(security.__name__, "masks", {}).get(func.__module__ + "." + func_name,
			                                                 getattr(func, "security",
			                                                         db.get(security.__name__, "default",
			                                                                security.DEFAULT_PERMISSIONS))) & bit
		return "checked" if ret else ""

	async def set_group(self, request):
		uid = await self.check_user(request)
		if uid is None:
			return web.Response(status=401)
		data = await request.json()
		if data.get("group", None) not in ("owner", "sudo", "support"):
			return web.Response(status=400)
		try:
			self.client_data[uid][2].set(security.__name__, data["group"],
			                             [int(user) for user in data["users"].split(",") if user])
		except (KeyError, ValueError):
			return web.Response(status=400)
		return web.Response()

	async def set_permission_set(self, request):
		uid = await self.check_user(request)
		if uid is None:
			return web.Response(status=401)
		data = await request.json()
		try:
			bit = security.BITMAP[data["bit"]]
		except KeyError:
			return web.Response(status=400)
		mod = self.client_data[uid][0].modules[int(data["mid"])]
		func = data["func"]
		db = self.client_data[uid][2]
		if mod and func:
			function = mod.commands[func]
			mask = db.get(security.__name__, "masks", {}).get(mod.__module__ + "." + function.__name__,
			                                                  getattr(function, "security",
			                                                          security.DEFAULT_PERMISSIONS))
		else:
			mask = db.get(security.__name__, "bounding_mask", security.DEFAULT_PERMISSIONS)
		try:
			if data["state"]:
				mask |= bit
			else:
				mask &= ~bit
		except KeyError:
			return web.Response(status=400)
		if mod and func:
			masks = self.client_data[uid][2].get(security.__name__, "masks", {})
			masks[mod.__module__ + "." + function.__name__] = mask
			self.client_data[uid][2].set(security.__name__, "masks", masks)
		else:
			self.client_data[uid][2].set(security.__name__, "bounding_mask", mask)
		return web.Response()
