#    Friendly Telegram Userbot
#    by GeekTG Team

import aiohttp_jinja2
import telethon
from aiohttp import web


class Web:
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.app.router.add_get("/", self.root)

	@aiohttp_jinja2.template("root.jinja2")
	async def root(self, request):
		uid = await self.check_user(request)
		if uid is None:
			return web.Response(status=302, headers={"Location": "/auth"})  # They gotta sign in.
		return {"uid": uid, "name": telethon.utils.get_display_name(await self.client_data[uid][1].get_me())}
