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
import json
import os

from .backend import CloudBackend
from .. import utils


class LocalBackend:
    def __init__(self, client, data_root):
        self._client = client
        self._data_root = data_root
        self._id = None
        self._file = None
        self._lock = asyncio.Lock()
        self._cloud_db = CloudBackend(client)

    async def init(self, trigger_refresh):
        # TODO: remove unused trigger_refresh
        await self._cloud_db.init(None)
        self._id = (await self._client.get_me(True)).user_id
        self._filename = os.path.join(self._data_root or os.path.dirname(utils.get_base_dir()),
                                      "database-{}.json".format(self._id))
        try:
            self._file = open(self._filename, "r+")
        except FileNotFoundError:
            self._file = open(self._filename, "w+")
            json.dump({}, self._file)

    def close(self):
        self._file.close()
        self._file = None

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
            self._file.truncate()
            self._file.write(data)
            self._file.flush()

    async def store_asset(self, message):
        return await self._cloud_db.store_asset(message)

    async def fetch_asset(self, id_):
        return await self._cloud_db.fetch_asset(id_)
