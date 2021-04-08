#    Friendly Telegram Userbot
#    by GeekTG Team

from aiohttp import web
import aiohttp_jinja2


class Web:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app.router.add_get("/translate", self.translate)

    @aiohttp_jinja2.template("translation.jinja2")
    async def translate(self, request):
        uid = await self.check_user(request)
        if uid is None:
            return web.Response(status=302, headers={"Location": "/"})  # They gotta sign in.
        return {"modules": self.client_data[uid][0].modules}
