from .. import loader, utils
import os
import json
import asyncio
from telethon.tl.functions.account import UpdateNotifySettingsRequest
from telethon.tl.types import InputPeerNotifySettings
from telethon.tl.functions.messages import GetScheduledHistoryRequest
import time

is_okteto = "OKTETO" in os.environ
BASE_DIR = "/data" if is_okteto else os.path.dirname(utils.get_base_dir())
oktetopath = os.path.join(BASE_DIR, "okteto.json")


@loader.tds
class OktetoMod(loader.Module):
    """Okteto pinger"""

    strings = {
        "name": "Okteto",
    }

    async def client_ready(self, client, db):
        self.db = db
        self.client = client
        self._bot = "@WebPageBot"
        if not is_okteto:
            raise loader.ModUnload("Module only works on Okteto")
        await client.edit_folder(self._bot, 1)
        await client(
            UpdateNotifySettingsRequest(
                peer=self._bot,
                settings=InputPeerNotifySettings(silent=True, mute_until=2147483647),
            )
        )

        with open(oktetopath, "r") as f:
            self.okteto_username = json.loads(f.read())["okteto"]
        self._task = asyncio.ensure_future(self.okteto_pinger())

    async def on_unload(self):
        self._task.cancel()

    async def okteto_pinger(self):
        async with self.client.conversation(self._bot, exclusive=False) as conv:
            lastsend = time.time()
            bothistory = (
                await self.client(GetScheduledHistoryRequest(peer=self._bot, hash=1))
            ).messages
            if bothistory:
                lastsend = max(time.mktime(msg.date.timetuple()) for msg in bothistory)
            lastsend += 86415
            for _ in range(5):
                await conv.send_message(
                    f"https://worker-{self.okteto_username}.cloud.okteto.net/?h={utils.rand(5)}",
                    schedule=lastsend,
                )
                lastsend += 86415
        return
