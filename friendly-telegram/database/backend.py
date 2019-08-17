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

from .. import utils

import atexit, logging, asyncio, telethon

from telethon.tl.functions.channels import CreateChannelRequest, DeleteChannelRequest
from telethon.tl.types import Message
from telethon.errors.rpcerrorlist import *

logger = logging.getLogger(__name__)

class CloudBackend():
    def __init__(self, client):
        self._client = client
        self._me = None
        self._db = None
    async def init(self, trigger_refresh):
        self._me = await self._client.get_me()
        self._callback = trigger_refresh
    async def _find_data_channel(self):
         async for dialog in self._client.iter_dialogs(None, ignore_migrated=True):
            if dialog.name == f"friendly-{self._me.id}-data" and dialog.is_channel:
                members = await self._client.get_participants(dialog, limit=2)
                if len(members) != 1:
                    continue
                logger.debug(f"Found data chat! It is {dialog}.")
                return dialog.entity
    async def _make_data_channel(self):
        return (await self._client(CreateChannelRequest(f"friendly-{self._me.id}-data", "// Don't touch", megagroup=True))).chats[0]
    async def do_download(self):
        """Attempt to download the database.
           Return the database (as unparsed JSON) or None"""
        if not self._db:
            self._db = await self._find_data_channel()
            if not self._db:
                logging.debug("No DB, returning")
                return None
            self._client.add_event_handler(self._callback, telethon.events.messageedited.MessageEdited(chats=[self._db]))

        msgs = self._client.iter_messages(
            entity=self._db,
            reverse=True
        )
        data = ""
        lastdata = ""
        async for msg in msgs:
            if isinstance(msg, Message):
                logger.debug(f"Found text message {msg}")
                data += lastdata
                lastdata = msg.message
            else:
                logger.debug(f"Found service message {msg}")
        logger.debug(f"Database contains {data}")
        return data

    async def do_upload(self, data):
        """Attempt to upload the database.
           Return True or throw"""
        if not self._db:
            self._db = await self._find_data_channel()
            if not self._db:
                self._db = await self._make_data_channel()
            self._client.add_event_handler(self._callback, telethon.events.messageedited.MessageEdited(chats=[self._db]))
        msgs = await self._client.get_messages(
            entity=self._db,
            reverse=True
        )
        ops = []
        sdata = data
        newmsg = False
        for msg in msgs:
            logger.debug(msg)
            if isinstance(msg, Message):
                if len(sdata):
                    logging.debug("editing message "+msg.stringify()+" last is "+msgs[-1].stringify())
                    if msg.id == msgs[-1].id:
                        newmsg = True
                    ops += [msg.edit(utils.escape_html(sdata[:4096]))]
                    sdata = sdata[4096:]
                else:
                    logging.debug("maybe deleting message")
                    if not msg.id == msgs[-1].id:
                        ops += [msg.delete()]
        try:
            await asyncio.gather(*ops)
        except MessageEditTimeExpiredError:
            logging.debug("Making new channel.")
            _db = self._db
            self._db = None
            await self._client(DeleteChannelRequest(channel=_db))
            return await self.do_upload(data)
        while len(sdata): # Only happens if newmsg is True or there was no message before
            newmsg = True
            await self._client.send_message(self._db, utils.escape_html(sdata[:4096]))
            sdata = sdata[4096:]
        if newmsg:
            await self._client.send_message(self._db, "Please ignore this chat.")
        return True
