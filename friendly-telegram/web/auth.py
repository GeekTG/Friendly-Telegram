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

#    Friendly Telegram Userbot
#    by GeekTG Team

import asyncio
import hashlib
import logging
import os
import secrets
from base64 import b64encode

import aiohttp_jinja2
from aiohttp import web

from .. import security

try:
	import humanfriendly.terminal.html
except ImportError:
	humanfriendly = False
	from telethon.extensions import html


class Web:
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._uid_to_code = {}
		self._secret_to_uid = {}
		self.app.router.add_get("/auth", self.auth)
		self.app.router.add_post("/sendCode", self.send_code)
		self.app.router.add_post("/code", self.check_code)
		self.app.router.add_get("/logOut", self.log_out)

	@aiohttp_jinja2.template("auth.jinja2")
	async def auth(self, request):
		if await self.check_user(request) is not None:
			return web.Response(status=302, headers={"Location": "/"})  # Already authenticated
		return {"users": self.client_data.keys(), "clients": bool(self.client_data)}

	async def send_code(self, request):
		uid = int(await request.text())
		if uid in self._uid_to_code.keys():
			return web.Response(body=self._uid_to_code[uid][1].decode("utf-8"))
		code = secrets.randbelow(100000)
		asyncio.ensure_future(asyncio.shield(self._clear_code(uid)))
		salt = b64encode(os.urandom(16))
		msg = ("Your code is <code>{:05d}</code>\nDo <b>not</b> share this code with anyone!\n"
		       "The code will expire in 2 minutes.".format(code))
		owners = self.client_data[uid][2].get(security.__name__, "owner", None) or ["me"]
		for owner in owners:
			try:
				await self.client_data[uid][1].send_message(owner, msg)
			except Exception:
				logging.warning("Failed to send code to owner", exc_info=True)
		print(humanfriendly.terminal.html.html_to_ansi(msg) if humanfriendly else html.parse(msg)[0])  # noqa: T001
		self._uid_to_code[uid] = (b64encode(hashlib.scrypt((str(code).zfill(5) + str(uid)).encode("utf-8"),
		                                                   salt=salt, n=16384, r=8, p=1, dklen=64)).decode("utf-8"),
		                          salt)
		return web.Response(body=salt.decode("utf-8"))

	async def _clear_code(self, uid):
		await asyncio.sleep(120)  # Codes last 2 minutes, or whenever they are used
		try:
			del self._uid_to_code[uid]
		except KeyError:
			pass  # Maybe the code has already been used

	async def check_code(self, request):
		code, uid = (await request.text()).split("\n")
		uid = int(uid)
		if uid not in self._uid_to_code:
			return web.Response(status=404)
		if self._uid_to_code[uid][0] == code:
			del self._uid_to_code[uid]
			if "DYNO" in os.environ:
				# Trust the X-Forwarded-For on Heroku, because all requests are proxied
				source = request.headers["X-Forwarded-For"]
			else:  # TODO allow other proxies to be supported
				source = request.transport.get_extra_info("peername")
				if source is not None:
					source = source[0]
			await self.client_data[uid][0].log("new_login", data=str(source))
			secret = secrets.token_urlsafe()
			asyncio.ensure_future(asyncio.shield(self._clear_secret(secret)))
			self._secret_to_uid[secret] = uid  # If they just signed in, they automatically are authenticated
			return web.Response(text=secret)
		else:
			return web.Response(status=401)

	async def _clear_secret(self, secret):
		await asyncio.sleep(60 * 60 * 6)  # You must authenticate once per 6 hours
		try:
			del self._secret_to_uid[secret]
		except KeyError:
			pass  # Meh.

	async def check_user(self, request):
		await asyncio.sleep(0.5)
		return self._secret_to_uid.get(request.cookies.get("secret", None), None)

	async def log_out(self, request):
		try:
			del self._secret_to_uid[request.cookies["secret"]]
		except KeyError:
			pass
		return web.Response(status=302, headers={"Location": "/"})
