# -*- coding: future_fstrings -*-

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
import json


class LocalBackend():
    def __init__(self, client):
        self._client = client
        self._id = None
        self._file = None
        self._lock = asyncio.Lock()

    async def init(self, trigger_refresh):
        self._id = (await self._client.get_me(True)).user_id
        self._filename = "database-{}.json".format(self._id)
        try:
            self._file = open(self._filename, "r+")
        except FileNotFoundError:
            self._file = open(self._filename, "w+")
            json.dump({}, self._file)

    async def do_download(self):
        """Attempt to download the database.
           Return the database (as unparsed JSON) or None"""
        async with self._lock:
            self._file.seek(0)
            return self._file.read()

    async def do_upload(self, data):
        """Attempt to upload the database.
           Return True or throw"""
        async with self._lock:
            self._file.seek(0)
            self._file.write(data)

    async def store_asset(self, message):
        pass

    async def fetch_asset(self, id):
        return None
