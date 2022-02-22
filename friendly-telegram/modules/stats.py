"""
    █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
    █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█

    Copyright 2022 t.me/hikariatama
    Licensed under the GNU GPLv3
"""

from .. import loader, utils
import logging
import time
from telethon.tl.types import *

logger = logging.getLogger(__name__)


@loader.tds
class StatsMod(loader.Module):
    """Stats for modules usage"""
    strings = {
        "name": "Stats",
        "stats": "📊 <b><u>Stats for last {}</u>:\n{}</b>"
    }

    async def client_ready(self, client, db):
        self.db = db
        self.client = client

    async def statscmd(self, message: Message) -> None:
        """[hour | day | week | month] - Get stats for chosen period"""
        args = utils.get_args_raw(message)
        stats = loader.dispatcher.stats

        args = args if args in ['hour', 'day', 'week', 'month'] else 'hour'
        offset = {
            'hour': 60 * 60,
            'day': 60 * 60 * 24,
            'week': 60 * 60 * 24 * 7,
            'month': 60 * 60 * 24 * 31
        }[args]

        res = ""
        for mod, stat in stats.items():
            count = len([_ for _ in stat if round(time.time()) - _ <= offset])
            if not count:
                continue
            if not any([module.strings('name') == mod for module in self.allmodules.modules]):
                continue

            res += f"   🔹 {mod}: {count} call(-s)\n"

        await utils.answer(message, self.strings('stats').format(args, res))
