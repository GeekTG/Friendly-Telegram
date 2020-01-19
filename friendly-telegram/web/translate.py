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


class Web:
    def __init__(self):
        super().__init__()
        self.app.router.add_get("/translate", self.translate)

    @aiohttp_jinja2.template("translation.jinja2")
    async def translate(self, request):
        uid = await self.check_user(request)
        if uid is None:
            return web.Response(status=302, headers={"Location": "/auth"})  # They gotta sign in.
        return {"modules": self.client_data[uid][0].modules}
