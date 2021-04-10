#    Friendly Telegram Userbot
#    by GeekTG Team

import asyncio
import logging

import telethon

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class NoCollisionsMod(loader.Module):
    """Makes sure only 1 userbot is running at a time"""
    strings = {"name": "Anti-collisions",
               "killed": "<b>All userbots killed</b>",
               "deadbeff": "<code>DEADBEEF</code>"}

    @loader.owner
    async def cleanbotscmd(self, message):
        """Kills all userbots except 1, selected according to which is fastest (approx)"""
        try:
            await utils.answer(message, self.strings("deadbeff", message))
            await asyncio.sleep(5)
            await utils.answer(message, self.strings("killed", message))
        except telethon.errors.rpcerrorlist.MessageNotModifiedError:
            [handler] = logging.getLogger().handlers
            handler.setLevel(logging.CRITICAL)
            for client in self.allclients:
                # Terminate main loop of all running clients
                # Won't work if not all clients are ready
                if client is not message.client:
                    await client.disconnect()
            await message.client.disconnect()
