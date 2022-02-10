"""
    Copyright 2021 t.me/innocoffee
    Licensed under the Apache License, Version 2.0
    
    Author is not responsible for any consequencies caused by using this
    software or any of its parts. If you have any questions or wishes, feel
    free to contact Dan by sending pm to @innocoffee_alt.
"""

#<3 title: Stats
#<3 pic: https://img.icons8.com/fluency/48/000000/voice-id.png
#<3 desc: Статистика выполнения модулей

from .. import loader, utils, main
import logging
import time

logger = logging.getLogger(__name__)


@loader.tds
class StatsMod(loader.Module):
    """Stats for modules usage for GeekTG only (won't work on classic FTG)"""
    strings = {
        "name": "Stats", 
        "update_required": "🚫 Please, make sure you have GeekTG correctly installed and it's latest version.",
        "stats": "📊 <b><u>Stats for last {}</u>:\n{}</b>"
    }

    async def client_ready(self, client, db):
        self.db = db
        self.client = client

    async def statscmd(self, message):
        """[hour | day | week | month] - Get stats for chosen period"""
        args = utils.get_args_raw(message)
        try:
            stats = loader.dispatcher.stats
        except AttributeError:
            return await utils.answer(message, self.strings('update_required'))

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
            if not count: continue
            res += f"   🔹 {mod}: {count} call(-s)\n"

        return await utils.answer(message, self.strings('stats').format(args, res))


