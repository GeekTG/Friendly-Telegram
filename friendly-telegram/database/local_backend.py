#    Friendly Telegram Userbot
#    by GeekTG Team

import asyncio
import json
import os

from .backend import CloudBackend
from .. import utils


class LocalBackend():
    def __init__(self, client, data_root):
        self._client = client
        self._data_root = data_root
        self._id = None
        self._file = None
        self._lock = asyncio.Lock()
        self._cloud_db = CloudBackend(client)

    async def init(self, trigger_refresh):
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

    async def fetch_asset(self, id):
        return await self._cloud_db.fetch_asset(id)
