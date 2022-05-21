import asyncio
import logging


from telethon.tl.custom import Message as CustomMessage
from telethon.tl.functions.channels import CreateChannelRequest, EditTitleRequest
from telethon.tl.types import Message
import json
import os

from .. import main, utils

is_okteto = "OKTETO" in os.environ

ORIGIN = "/data" if is_okteto else "/".join(main.__file__.split("/")[:-2])

logger = logging.getLogger(__name__)


class CloudBackend:
    def __init__(self, client):
        self._client = client
        self._me = None
        self.db = None
        self._assets = None
        self._anti_double_lock = asyncio.Lock()
        self._anti_double_asset_lock = asyncio.Lock()
        self._data_already_exists = False
        self._assets_already_exists = False
        self.close = lambda: None

    async def init(self, trigger_refresh):
        self._me = await self._client.get_me(True)
        self._db_path = os.path.join(ORIGIN, f"config-{self._me.user_id}.json")
        self._callback = trigger_refresh

    async def _find_asset_channel(self):
        async for dialog in self._client.iter_dialogs(None, ignore_migrated=True):
            if (
                dialog.name == f"friendly-{self._me.user_id}-assets"
                and dialog.is_channel
            ):
                members = await self._client.get_participants(dialog, limit=2)
                if len(members) != 1:
                    continue
                logger.debug(f"Found asset chat! It is {dialog.id}.")
                return dialog.entity

    async def _make_asset_channel(self):
        async with self._anti_double_asset_lock:
            if self._assets_already_exists:
                return await self._find_data_channel()
            self._assets_already_exists = True
            return (
                await self._client(
                    CreateChannelRequest(
                        f"friendly-{self._me.user_id}-assets",
                        "// Don't touch",
                        megagroup=True,
                    )
                )
            ).chats[0]

    async def do_download(self):
        """
        Attempt to download the database.
        Return the database (as unparsed JSON) or None
        """

        is_base_saved = False
        try:
            with open(self._db_path, "r", encoding="utf-8") as f:
                data = json.dumps(json.loads(f.read()))
            is_base_saved = True
        except Exception:
            data = {}

        if not is_base_saved:
            chat = [
                chat
                async for chat in self._client.iter_dialogs(None, ignore_migrated=True)
                if chat.name == f"friendly-{self._me.user_id}-data" and chat.is_channel
            ]
            if not chat:
                await self.do_upload(data)
                return data
            await self._client(
                EditTitleRequest(channel=chat[0], title=f"old-{self._me.user_id}-data")
            )
            logger.info("Syncing database...")
            msgs = self._client.iter_messages(entity=chat[0], reverse=True)

            data = ""
            lastdata = ""

            async for msg in msgs:
                if isinstance(msg, Message):
                    data += lastdata
                    lastdata = msg.message
                else:
                    logger.debug(f"Found service message {msg}")
            await self.do_upload(data)

        return data

    async def do_upload(self, data):
        """
        Attempt to upload the database.
        Return True or throw
        """

        try:
            with open(self._db_path, "w", encoding="utf-8") as f:
                f.write(data or "{}")
        except Exception:
            logger.exception("Database save failed!")
            raise

        return True

    async def store_asset(self, message):
        if not self._assets:
            self._assets = await self._find_asset_channel()

        if not self._assets:
            self._assets = await self._make_asset_channel()

        return (
            (await self._client.send_message(self._assets, message)).id
            if isinstance(message, (Message, CustomMessage))
            else (
                await self._client.send_message(
                    self._assets, file=message, force_document=True
                )
            ).id
        )

    async def fetch_asset(self, id_):
        if not self._assets:
            self._assets = await self._find_asset_channel()

        if not self._assets:
            return None

        ret = await self._client.get_messages(self._assets, ids=[id_])

        if not ret:
            return None

        return ret[0]
