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

import asyncio
from aiohttp import web
import aiohttp_jinja2
import hashlib
import secrets

from base64 import b64encode


class Web:
    def __init__(self):
        super().__init__()
        self._uid_to_code = {}
        self._secret_to_uid = {}
        self.app.router.add_get("/auth", self.auth)
        self.app.router.add_post("/sendCode", self.send_code)
        self.app.router.add_post("/code", self.check_code)

    @aiohttp_jinja2.template("auth.jinja2")
    async def auth(self, request):
        if await self.check_user(request) is not None:
            return web.Response(status=302, headers={"Location": "/"})  # Already authenticated
        return {"users": self.client_data.keys()}

    async def send_code(self, request):
        uid = int(await request.text())
        if uid in self._uid_to_code.keys():
            return web.Response()
        code = secrets.randbelow(100000)
        asyncio.ensure_future(asyncio.shield(self._clear_code(uid)))
        self._uid_to_code[uid] = b64encode(hashlib.scrypt((str(code).zfill(5) + str(uid)).encode("utf-8"),
                                                          salt="friendlytgbot".encode("utf-8"),
                                                          n=16384, r=8, p=1, dklen=64)).decode("utf-8")
        await self.client_data[uid][1].send_message("me", "Your code is <code>{:05d}</code>\nDo <b>not</b> "
                                                          "share this code with anyone, even is they say they are"
                                                          " from friendly-telegram.\nThe code will expire in "
                                                          "2 minutes.".format(code))
        return web.Response()

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
        if self._uid_to_code[uid] == code:
            del self._uid_to_code[uid]
            secret = secrets.token_urlsafe()
            asyncio.ensure_future(asyncio.shield(self._clear_secret(secret)))
            self._secret_to_uid[secret] = uid
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
