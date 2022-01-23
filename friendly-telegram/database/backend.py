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

from .. import utils, main

import logging
import asyncio
import telethon
import time
import os
import json

from telethon.tl.functions.channels import CreateChannelRequest, DeleteChannelRequest
from telethon.tl.types import Message
from telethon.tl.custom import Message as CustomMessage
from telethon.errors.rpcerrorlist import MessageEditTimeExpiredError, MessageNotModifiedError

logger = logging.getLogger(__name__)

ORIGIN = '/'.join(main.__file__.split('/')[:-2])

class CloudBackend():
    def __init__(self, client):
        self._client = client
        self._me = None
        self.db = None
        self._assets = None
        self._anti_double_lock = asyncio.Lock()
        self._anti_double_asset_lock = asyncio.Lock()
        self._data_already_exists = False
        self._assets_already_exists = False

    async def init(self, trigger_refresh):
        self._me = await self._client.get_me(True)
        self._db_path = os.path.join(ORIGIN, f'config-{self._me.user_id}.json')
        self._callback = trigger_refresh

    def close(self):
        pass

    async def _find_data_channel(self):
        async for dialog in self._client.iter_dialogs(None, ignore_migrated=True):
            if dialog.name == f"friendly-{self._me.user_id}-data" and dialog.is_channel:
                members = await self._client.get_participants(dialog, limit=2)
                if len(members) != 1:
                    continue
                logger.debug(f"Found data chat! It is {dialog.id}.")
                return dialog.entity

    async def _make_data_channel(self):
        async with self._anti_double_lock:
            if self._data_already_exists:
                return await self._find_data_channel()
            self._data_already_exists = True
            return (await self._client(CreateChannelRequest(f"friendly-{self._me.user_id}-data",
                                                            "// Don't touch", megagroup=True))).chats[0]

    async def do_download_tg(self):
        # TODO: PEP 8: E101 indentation contains mixed spaces and tabs
        """Attempt to download the database.
        Return the database (as unparsed JSON)"""
        if not self.db:
            self.db = await self._find_data_channel()
            if not self.db:
                logging.debug("No DB, returning")
                return '{}'

        msgs = self._client.iter_messages(
            entity=self.db,
            reverse=True
        )
        data = ""
        lastdata = ""
        async for msg in msgs:
            if isinstance(msg, Message):
                data += lastdata
                lastdata = msg.message
            else:
                logger.debug(f"Found service message {msg}")
        return data

    async def _find_asset_channel(self):
        async for dialog in self._client.iter_dialogs(None, ignore_migrated=True):
            if dialog.name == f"friendly-{self._me.user_id}-assets" and dialog.is_channel:
                members = await self._client.get_participants(dialog, limit=2)
                if len(members) != 1:
                    continue
                logger.debug(f"Found asset chat! It is {dialog.id}.")
                return dialog.entity

    async def _make_asset_channel(self):
        async with self._anti_double_asset_lock:
            if not self._assets_already_exists:
                self._assets_already_exists = True
                return (await self._client(CreateChannelRequest(f"friendly-{self._me.user_id}-assets",
                                                                "// Don't touch", megagroup=True))).chats[0]
            else:
                return await self._find_data_channel()

    async def do_download(self):
        """Attempt to download the database.
           Return the database (as unparsed JSON) or None"""

        try:
            data = json.dumps(json.loads(open(self._db_path, 'r', encoding="utf-8").read()))
        except:
            data = await self.do_download_tg()
            # raise

        return data

    async def do_upload(self, data):
        """Attempt to upload the database.
           Return True or throw"""
        try:
            open(self._db_path, 'w', encoding='utf-8').write(data)
        except:
            logger.exception("Database save failed!")
            raise

        return True

    async def store_asset(self, message):
        if not self._assets:
            self._assets = await self._find_asset_channel()
        if not self._assets:
            self._assets = await self._make_asset_channel()
        return ((await self._client.send_message(self._assets, message)).id
                if isinstance(message, (Message, CustomMessage)) else
                (await self._client.send_message(self._assets, file=message, force_document=True)).id)

    async def fetch_asset(self, id):
        if not self._assets:
            self._assets = await self._find_asset_channel()
        if not self._assets:
            return None
        ret = (await self._client.get_messages(self._assets, limit=1, max_id=id + 1, min_id=id - 1))
        if not ret:
            return None
        return ret[0]
