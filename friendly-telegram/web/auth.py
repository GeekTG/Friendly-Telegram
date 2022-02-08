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

# Modded by GeekNet team, t.me/hikariatama

import asyncio
from aiohttp import web
import aiohttp_jinja2
import hashlib
import os
import secrets
import logging
import telethon

logger = logging.getLogger(__name__)

from base64 import b64encode

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
        self._code_to_ms = {}
        self.app.router.add_get("/auth", self.auth)
        self.app.router.add_post("/sendCode", self.send_code)
        self.app.router.add_post("/code", self.check_code)
        self.app.router.add_get("/logOut", self.log_out)
        self.app.router.add_post("/dlmod", self.dlmod)
        self.app.router.add_post("/unloadmod", self.unloadmod)
        self.app.router.add_get("/modules", self.modules)

    @aiohttp_jinja2.template("auth.jinja2")
    async def auth(self, request):
        if await self.check_user(request) is not None:
            return web.Response(status=302, headers={"Location": "/"})  # Already authenticated
        return {
            "users": {
                uid: telethon.utils.get_display_name(await _client[1].get_me())
                for uid, _client in self.client_data.items()
            },
            "clients": bool(self.client_data)
        }

    async def modules(self, request):
        uid = self._secret_to_uid[request.cookies["secret"]]

        return web.json_response([
            {
                'origin': getattr(mod, '__origin__', False) or '<file>',
                'name': getattr(mod, 'name', False) or mod.strings['name'],
                'dir': dir(mod),
                'docs': getattr(mod, '__doc__', False) or 'No docs :(',
                'config': [{
                    'param': param,
                    'doc': mod.config.getdoc(param),
                    'default': mod.config.getdef(param),
                    'current': mod.config[param]
                } for param in mod.config] if getattr(mod, 'config', False) else []
            }

            for mod in self.client_data[uid][0].modules
        ])


    async def dlmod(self, request):
        mod = await request.text()
        uid = self._secret_to_uid[request.cookies["secret"]]

        msg = await self.client_data[uid][1].send_message('me', f'.dlmod {mod}')

        await self.client_data[uid][0].commands['dlmod'](msg)

        result = (await self.client_data[uid][1].get_messages('me', msg.id))[0].raw_text
        await msg.delete()

        return web.Response(status=200, text=result)

    async def unloadmod(self, request):
        mod = await request.text()
        uid = self._secret_to_uid[request.cookies["secret"]]

        msg = await self.client_data[uid][1].send_message('me', f'.unloadmod {mod}')

        await self.client_data[uid][0].commands['unloadmod'](msg)

        result = (await self.client_data[uid][1].get_messages('me', msg.id))[0].raw_text
        await msg.delete()

        return web.Response(status=200, text=result)

    async def send_code(self, request):
        uid = int(await request.text())
        if uid in self._uid_to_code.keys():
            return web.Response(body=self._uid_to_code[uid][1])
        code = secrets.randbelow(100000)
        asyncio.ensure_future(asyncio.shield(self._clear_code(uid)))
        salt = b64encode(os.urandom(16))
        msg = ("Your GeekTG Auth code: <code>{:05d}</code>\nDo <b>not</b> share it with <b>anyone</b>!".format(code))
        owners = self.client_data[uid][2].get(security.__name__, "owner", None) or ["me"]
        msgs = []
        for owner in owners:
            try:
                msgs += [await self.client_data[uid][1].send_message(owner, msg)]
            except Exception:
                logging.warning("Failed to send code to owner", exc_info=True)
        print(humanfriendly.terminal.html.html_to_ansi(msg) if humanfriendly else html.parse(msg)[0])  # noqa: T001
        self._uid_to_code[uid] = str(code).zfill(5)
        self._code_to_ms[str(code)] = msgs
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
        if str(self._uid_to_code[uid]) != str(code):
            return web.Response(status=401)
        del self._uid_to_code[uid]
        for msg in self._code_to_ms[str(code)]:
            try:
                await msg.delete()
            except Exception:
                pass
        del self._code_to_ms[str(code)]
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
