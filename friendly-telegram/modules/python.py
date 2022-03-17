"""
    █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
    █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█

    Copyright 2022 t.me/hikariatama
    Licensed under the GNU GPLv3
"""

import logging
import telethon
from meval import meval
from .. import loader, utils
from traceback import format_exc
import itertools
from types import ModuleType
from telethon.tl.types import Message

logger = logging.getLogger(__name__)


@loader.tds
class PythonMod(loader.Module):
    """Evaluates python code"""

    strings = {
        "name": "Python",
        "eval": "<b>🎬 Code:</b>\n<code>{}</code>\n<b>🪄 Result:</b>\n<code>{}</code>",
        "err": "<b>🎬 Code:</b>\n<code>{}</code>\n\n<b>🚫 Error:</b>\n<code>{}</code>",
    }

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

    def lookup(self, modname: str):
        return next(
            (
                mod
                for mod in self.allmodules.modules
                if mod.name.lower() == modname.lower()
            ),
            False,
        )

    @loader.owner
    async def evalcmd(self, message: Message) -> None:
        """Alias for .e command"""
        await self.ecmd(message)
        return

    @loader.owner
    async def ecmd(self, message: Message) -> None:
        """MEvaluates python code"""
        phone = self.client.phone
        ret = self.strings("eval", message)
        try:
            it = await meval(
                utils.get_args_raw(message), globals(), **await self.getattrs(message)
            )
        except Exception:
            exc = format_exc().replace(phone, "📵")
            await utils.answer(
                message,
                self.strings("err", message).format(
                    utils.escape_html(utils.get_args_raw(message)),
                    utils.escape_html(exc),
                ),
            )

            return
        ret = ret.format(
            utils.escape_html(utils.get_args_raw(message)), utils.escape_html(it)
        )
        ret = ret.replace(str(phone), "📵")
        await utils.answer(message, ret)

    async def getattrs(self, message):
        return {
            "message": message,
            "client": self.client,
            "self": self,
            "db": self.db,
            "reply": await message.get_reply_message(),
            **self.get_sub(telethon.tl.types),
            **self.get_sub(telethon.tl.functions),
            "event": message,
            "chat": message.to_id,
            "telethon": telethon,
            "utils": utils,
            "f": telethon.tl.functions,
            "c": self.client,
            "m": message,
            "loader": loader,
            "lookup": self.lookup,
        }

    def get_sub(self, it, _depth: int = 1) -> dict:
        """Get all callable capitalised objects in an object recursively, ignoring _*"""
        return {
            **dict(
                filter(
                    lambda x: x[0][0] != "_"
                    and x[0][0].upper() == x[0][0]
                    and callable(x[1]),
                    it.__dict__.items(),
                )
            ),
            **dict(
                itertools.chain.from_iterable(
                    [
                        self.get_sub(y[1], _depth + 1).items()
                        for y in filter(
                            lambda x: x[0][0] != "_"
                            and isinstance(x[1], ModuleType)
                            and x[1] != it
                            and x[1].__package__.rsplit(".", _depth)[0]
                            == "telethon.tl",
                            it.__dict__.items(),
                        )
                    ]
                )
            ),
        }
