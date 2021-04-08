#    Friendly Telegram Userbot
#    by GeekTG Team

import ast

from aiohttp import web
import aiohttp_jinja2


class Web:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app.router.add_get("/config", self.config)
        self.app.router.add_put("/setConfig", self.set_config)

    @aiohttp_jinja2.template("config.jinja2")
    async def config(self, request):
        uid = await self.check_user(request)
        if uid is None:
            return web.Response(status=302, headers={"Location": "/"})  # They gotta sign in.
        return {"modules": self.client_data[uid][0].modules}

    async def set_config(self, request):
        uid = await self.check_user(request)
        if uid is None:
            return web.Response(status=401)
        data = await request.json()
        mid, key, value = int(data["mid"]), data["key"], data["value"]
        mod = self.client_data[uid][0].modules[mid]
        if value:
            try:
                value = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                pass
            self.client_data[uid][2].setdefault(mod.__module__, {}).setdefault("__config__", {})[key] = value
        else:
            try:
                del self.client_data[uid][2].setdefault(mod.__module__, {}).setdefault("__config__", {})[key]
            except KeyError:
                pass
        self.client_data[uid][0].send_config_one(mod, self.client_data[uid][2], skip_hook=True)
        self.client_data[uid][2].save()
        return web.Response()
