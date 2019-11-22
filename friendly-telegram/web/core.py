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

from aiohttp import web
import aiohttp_jinja2
import collections
import jinja2
import inspect
import asyncio
import secrets
import telethon
import hashlib
from base64 import b64encode
import time
import os


@web.middleware
async def ratelimit(request, handler):
    storage = handler.__func__
    if not hasattr(storage, "_ratelimit"):
        storage._ratelimit = collections.defaultdict(lambda: 0)
        storage._ratelimit_last = collections.defaultdict(lambda: 1)
        storage._last_request = collections.defaultdict(lambda: 0)
    if storage._last_request[request.remote] > time.time() - 30:
        # Maybe ratelimit, was requested within 30 seconds
        last = storage._ratelimit_last[request.remote]
        storage._ratelimit_last[request.remote] = storage._ratelimit[request.remote]
        storage._ratelimit[request.remote] += last
        if storage._ratelimit[request.remote] > 50:
            # If they have to wait more than 5 seconds (10 requests), kill em.
            return web.Response(status=429)
        await asyncio.sleep(storage._ratelimit[request.remote] / 10)
    else:
        try:
            del storage._ratelimit[request.remote]
            del storage._ratelimit_last[request.remote]
        except KeyError:
            pass
    storage._last_request[request.remote] = time.time()
    return await handler(request)


class Web:
    def __init__(self):
        self.auth_lock = asyncio.Lock()
        self.loaders_clients_dbs = {}
        self.app = web.Application(middlewares=[ratelimit])
        self.uid_to_code = {}
        self.secret_to_uid = {}
        aiohttp_jinja2.setup(self.app, filters={"getdoc": inspect.getdoc, "ascii": ascii},
                             loader=jinja2.FileSystemLoader("web-resources"))
        self.app["static_root_url"] = "/static"
        self.app.router.add_get("/", self.root)
        self.app.router.add_get("/config", self.config)
        self.app.router.add_put("/setConfig", self.set_config)
        self.app.router.add_get("/auth", self.auth)
        self.app.router.add_post("/sendCode", self.send_code)
        self.app.router.add_post("/code", self.check_code)
        self.app.router.add_static("/static/", "web-resources/static")

    def start_if_ready(self, total_count):
        return asyncio.gather(asyncio.gather()) if total_count > len(self.loaders_clients_dbs) else self.start()

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, None, os.environ.get("PORT", 8080))
        return asyncio.ensure_future(site.start())

    async def add_loader(self, client, loader, db):
        self.loaders_clients_dbs[(await client.get_me(True)).user_id] = (loader, client, db)

    @aiohttp_jinja2.template("root.jinja2")
    async def root(self, request):
        uid = await self._check_user(request)
        if uid is None:
            return web.Response(status=302, headers={"Location": "/auth"})  # They gotta sign in.
        return {"uid": uid, "name": telethon.utils.get_display_name(await self.loaders_clients_dbs[uid][1].get_me())}

    @aiohttp_jinja2.template("config.jinja2")
    async def config(self, request):
        uid = await self._check_user(request)
        if uid is None:
            return web.Response(status=302, headers={"Location": "/auth"})  # They gotta sign in.
        return {"modules": self.loaders_clients_dbs[uid][0].modules}

    async def set_config(self, request):
        uid = await self._check_user(request)
        if uid is None:
            return web.Response(status=401)
        data = await request.json()
        mid, key, value = int(data["mid"]), data["key"], data["value"]
        mod = self.loaders_clients_dbs[uid][0].modules[mid]
        if value:
            self.loaders_clients_dbs[uid][2].setdefault(mod.__module__, {}).setdefault("__config__", {})[key] = value
        else:
            try:
                del self.loaders_clients_dbs[uid][2].setdefault(mod.__module__, {}).setdefault("__config__", {})[key]
            except KeyError:
                pass
        self.loaders_clients_dbs[uid][0].send_config_one(mod, self.loaders_clients_dbs[uid][2], True)
        self.loaders_clients_dbs[uid][2].save()
        return web.Response()

    @aiohttp_jinja2.template("auth.jinja2")
    async def auth(self, request):
        if await self._check_user(request) is not None:
            return web.Response(status=302, headers={"Location": "/"})  # Already authenticated
        return {"users": self.loaders_clients_dbs.keys()}

    async def send_code(self, request):
        uid = int(await request.text())
        if uid in self.uid_to_code.keys():
            return web.Response()
        code = secrets.randbelow(100000)
        asyncio.ensure_future(asyncio.shield(self._clear_code(uid)))
        self.uid_to_code[uid] = b64encode(hashlib.scrypt((str(code).zfill(5) + str(uid)).encode("utf-8"),
                                                         salt="friendlytgbot".encode("utf-8"),
                                                         n=16384, r=8, p=1, dklen=64)).decode("utf-8")
        await self.loaders_clients_dbs[uid][1].send_message("me", "Your code is <code>{:05d}</code>\nDo <b>not</b> "
                                                            "share this code with anyone, even is they say they are"
                                                            " from friendly-telegram.\nThe code will expire in "
                                                            "2 minutes.".format(code))
        return web.Response()

    async def _clear_code(self, uid):
        await asyncio.sleep(120)  # Codes last 2 minutes, or whenever they are used
        try:
            del self.uid_to_code[uid]
        except KeyError:
            pass  # Maybe the code has already been used

    async def check_code(self, request):
        code, uid = (await request.text()).split("\n")
        uid = int(uid)
        if uid not in self.uid_to_code:
            return web.Response(status=404)
        if self.uid_to_code[uid] == code:
            del self.uid_to_code[uid]
            secret = secrets.token_urlsafe()
            asyncio.ensure_future(asyncio.shield(self._clear_secret(secret)))
            self.secret_to_uid[secret] = uid
            return web.Response(text=secret)
        else:
            return web.Response(status=401)

    async def _clear_secret(self, secret):
        await asyncio.sleep(60 * 60 * 6)  # You must authenticate once per 6 hours
        try:
            del self.secret_to_uid[secret]
        except KeyError:
            pass  # Meh.

    async def _check_user(self, request):
        await asyncio.sleep(0.5)
        return self.secret_to_uid.get(request.cookies.get("secret", None), None)
