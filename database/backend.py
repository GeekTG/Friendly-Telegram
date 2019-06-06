import atexit, logging, asyncio

from telethon.tl.functions.channels import CreateChannelRequest
from telethon.tl.types import Message
from telethon.errors.rpcerrorlist import *

logger = logging.getLogger(__name__)

class CloudBackend():
    def __init__(self, client):
        self._client = client
        self._me = None
        self._db = None
    async def init(self):
        self._me = await self._client.get_me()
    async def _find_data_channel(self):
         async for dialog in self._client.iter_dialogs(None, ignore_migrated=True):
            if dialog.name == f"friendly-{self._me.id}-data" and dialog.is_channel:
                members = await self._client.get_participants(dialog, limit=2)
                if len(members) != 1:
                    continue
                logger.debug(f"Found data chat! It is {dialog}.")
                return dialog.entity
    async def _make_data_channel(self):
        return (await self._client(CreateChannelRequest(f"friendly-{self._me.id}-data", "// Don't touch", megagroup=False))).chats[0]
    async def do_download(self):
        """Attempt to download the database.
           Return the database (as unparsed JSON) or None"""
        if not self._db:
            self._db = await self._find_data_channel()
        if not self._db:
            return None

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
        newmsg = False
        if not self._db:
            self._db = await self._find_data_channel()
        if not self._db:
            newmsg = True
            self._db = await self._make_data_channel()
        msgs = await self._client.get_messages(
            entity=self._db,
            reverse=True
        )
        ops = []
        if not newmsg:
            for msg in msgs[:-1]:
                logger.debug(msg)
                if not isinstance(msg, Message):
                    continue
                if len(data):
                    if msg.message != data[:4096]:
                        await msg.edit(data[:4096])
                    logger.debug(data)
                    data = data[4096:]
                    logger.debug(data)
                else:
                    logger.debug("deleting")
                    await msg.delete()
        if len(data):
            newmsg = True
            await msgs[-1].delete()
        while len(data):
            await self._client.send_message(self._db, data[:4096])
            data = data[4096:]
        if newmsg:
            await self._client.send_message(self._db, "Please ignore this chat.")
        return True
