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
