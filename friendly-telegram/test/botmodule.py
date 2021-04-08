#    Friendly Telegram Userbot
#    by GeekTG Team

import asyncio
import humanfriendly
import logging

from telethon.tl.functions.account import DeleteAccountRequest

from ..test import core
from .. import loader

logger = logging.getLogger(__name__)


@loader.tds
class BotTestMod(loader.Module):
    """Testing coordinator (bot half)"""
    strings = {"name": "Test Coordinator (bot)"}

    async def client_ready(self, client, db):
        stage = db.get(core.__name__, "stage", 0)
        await db.set(core.__name__, "stage", stage + 1)
        self._client = client
        self._db = db

    @loader.unrestricted
    async def startcmd(self, message):
        """Begin testing"""
        stage = self._db.get(core.__name__, "stage", 0)
        total = sum(hasattr(c, "test") for c in core.user_modules.commands.values())
        i = 0
        with humanfriendly.Spinner(label="Testing (stage {})".format(stage), total=total) as spinner:
            for name, func in core.user_modules.commands.items():
                if hasattr(func, "test"):
                    spinner.step(progress=i)
                    i += 1
                    try:
                        await func.test(message.input_chat, self._db, self._client, name)
                    except Exception:
                        logging.exception("Test failed: %r (in stage %d)", name, stage)
                    await asyncio.sleep(2)
        core.TestManager.restart.set_result(None)
        if stage == 5:
            try:
                # W606 is a false positive
                await [c for c in self.allclients if c is not self._client][0](DeleteAccountRequest(""))  # noqa: W606
            except asyncio.CancelledError:
                exit()
