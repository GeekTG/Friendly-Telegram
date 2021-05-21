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

import asyncio
import collections
import inspect
import os
import time

import aiohttp_jinja2
import jinja2
from aiohttp import web

from . import initial_setup, root, auth, translate, config, settings


def ratelimit(get_storage, secret_to_uid):
	@web.middleware
	async def ratelimit_middleware(request, handler):
		storage = get_storage(handler)
		if not hasattr(storage, "_ratelimit"):
			storage.setdefault("ratelimit", collections.defaultdict(lambda: 0))
			storage.setdefault("ratelimit_last", collections.defaultdict(lambda: 1))
			storage.setdefault("last_request", collections.defaultdict(lambda: 0))
		if storage["last_request"][request.remote] > time.time() - 30:
			# Maybe ratelimit, was requested within 30 seconds
			if "secret" in request.cookies:
				if storage["ratelimit"][request.remote] > 50:
					return web.Response(status=429)
				await asyncio.sleep(storage["ratelimit"][request.remote] / 10)
				if secret_to_uid(request.cookies["secret"]) is not None:
					return await handler(request)  # don't ratelimit authenticated requests
			last = storage["ratelimit_last"][request.remote]
			storage["ratelimit_last"][request.remote] = storage["ratelimit"][request.remote]
			storage["ratelimit"][request.remote] += last
			if storage["ratelimit"][request.remote] > 50:
				# If they have to wait more than 5 seconds (10 requests), kill em.
				return web.Response(status=429)
			await asyncio.sleep(storage["ratelimit"][request.remote] / 10)
		else:
			try:
				del storage["ratelimit"][request.remote]
				del storage["ratelimit_last"][request.remote]
			except KeyError:
				pass
		storage["last_request"][request.remote] = time.time()
		return await handler(request)

	return ratelimit_middleware


class Web(initial_setup.Web, root.Web, auth.Web, translate.Web, config.Web, settings.Web):
	def __init__(self, **kwargs):
		self.runner = None
		self.port = None
		self.running = asyncio.Event()
		self.ready = asyncio.Event()
		self.client_data = {}
		self._ratelimit_data = collections.defaultdict(dict)
		self.app = web.Application(middlewares=[ratelimit(lambda f: self._ratelimit_data[f],
		                                                  lambda s: self._secret_to_uid.get(s, None))])
		aiohttp_jinja2.setup(self.app, filters={"getdoc": inspect.getdoc, "ascii": ascii},
		                     loader=jinja2.FileSystemLoader("web-resources"))
		self.app["static_root_url"] = "/static"
		super().__init__(**kwargs)
		self.app.router.add_static("/static/", "web-resources/static")
		self.app.router.add_get("/favicon.ico", self.favicon)

	async def start_if_ready(self, total_count, port):
		if total_count <= len(self.client_data):
			if not self.running.is_set():
				await self.start(port)
			self.ready.set()

	async def start(self, port):
		self.runner = web.AppRunner(self.app)
		await self.runner.setup()
		self.port = os.environ.get("PORT", port)
		site = web.TCPSite(self.runner, None, self.port)
		await site.start()
		self.running.set()

	async def stop(self):
		await self.runner.shutdown()
		await self.runner.cleanup()
		self.running.clear()
		self.ready.clear()

	async def add_loader(self, client, loader, db):
		self.client_data[(await client.get_me(True)).user_id] = (loader, client, db)

	async def favicon(self, request):
		return web.Response(status=301, headers={"Location": "https://friendly-telegram.gitlab.io/favicon.ico"})
