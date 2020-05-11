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

import logging
import time

from io import BytesIO

from .. import loader, utils

logger = logging.getLogger(__name__)


def register(cb):
    cb(TestMod())


@loader.tds
class TestMod(loader.Module):
    """Self-tests"""
    strings = {"name": "Tester",
               "pong": "Pong",
               "bad_loglevel": ("<b>Invalid loglevel. Please refer to </b>"
                                "<a href='https://docs.python.org/3/library/logging.html#logging-levels'>"
                                "the docs</a><b>.</b>"),
               "set_loglevel": "<b>Please specify verbosity as an integer or string</b>",
               "uploading_logs": "<b>Uploading logs...</b>",
               "no_logs": "<b>You don't have any logs at verbosity {}.</b>",
               "logs_filename": "ftg-logs.txt",
               "logs_caption": "friendly-telegram logs with verbosity {}",
               "suspend_invalid_time": "<b>Invalid time to suspend</b>"}

    @loader.unrestricted
    async def pingcmd(self, message):
        """Does nothing"""
        await utils.answer(message, self.strings("pong", message))

    async def dumpcmd(self, message):
        """Use in reply to get a dump of a message"""
        if not message.is_reply:
            return
        await utils.answer(message, "<code>"
                           + utils.escape_html((await message.get_reply_message()).stringify()) + "</code>")

    async def logscmd(self, message):
        """.logs <level>
           Dumps logs. Loglevels below WARNING may contain personal info."""
        args = utils.get_args(message)
        if not len(args) == 1:
            await utils.answer(message, self.strings("set_loglevel", message))
            return
        try:
            lvl = int(args[0])
        except ValueError:
            # It's not an int. Maybe it's a loglevel
            lvl = getattr(logging, args[0].upper(), None)
        if not isinstance(lvl, int):
            await utils.answer(message, self.strings("bad_loglevel", message))
            return
        [handler] = logging.getLogger().handlers
        logs = ("\n".join(handler.dumps(lvl))).encode("utf-8")
        if not len(logs) > 0:
            await utils.answer(message, self.strings("no_logs", message).format(lvl))
            return
        logs = BytesIO(logs)
        logs.name = self.strings("logs_filename", message)
        await utils.answer(message, logs, caption=self.strings("logs_caption", message).format(lvl))

    @loader.owner
    async def suspendcmd(self, message):
        """.suspend <time>
           Suspends the bot for N seconds"""
        # Blocks asyncio event loop, preventing ANYTHING happening (except multithread ops,
        # but they will be blocked on return).
        try:
            time.sleep(int(utils.get_args_raw(message)))
        except ValueError:
            await utils.answer(message, self.strings("suspend_invalid_time", message))

    async def client_ready(self, client, db):
        self.client = client
