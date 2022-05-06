from .. import loader, utils
import os
import json
import asyncio
from telethon.tl.functions.account import UpdateNotifySettingsRequest
from telethon.tl.types import InputPeerNotifySettings

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
            raise loader.LoadError("This module is only available on Okteto")
        await client.edit_folder(self._bot, 1)
        await client(
            UpdateNotifySettingsRequest(
                peer=self._bot,
                settings=InputPeerNotifySettings(silent=True, mute_until=2147483647),
            )
        )

        self.okteto_username = json.loads(open(oktetopath, "r").read())["okteto"]
        self._task = asyncio.ensure_future(self.okteto_pinger())

    async def on_unload(self):
        self._task.cancel()

    async def okteto_pinger(self):
        async with self.client.conversation(self._bot, exclusive=False) as conv:
            while True:
                m = await conv.send_message(
                    f"https://worker-{self.okteto_username}.cloud.okteto.net/"
                )
                try:
                    r = await conv.get_response()
                except Exception:
                    break
                r2 = await conv.get_response()
                if "Link previews was updated successfully" in r.raw_text:
                    for msg in [m, r, r2]:
                        await msg.delete()
                await asyncio.sleep(43200)
        return
