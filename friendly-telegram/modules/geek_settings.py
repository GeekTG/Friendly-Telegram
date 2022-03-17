"""
    █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
    █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
    Copyright 2022 t.me/hikariatama
    Licensed under the Creative Commons CC BY-NC-ND 4.0

    Full license text can be found at:
    https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode

    Human-friendly one:
    https://creativecommons.org/licenses/by-nc-nd/4.0
"""

# meta pic: https://img.icons8.com/fluency/48/000000/settings.png
# scope: geektg_only

from .. import loader, utils, main
import logging
from telethon.tl.types import Message

logger = logging.getLogger(__name__)


@loader.tds
class AdvancedSettingsMod(loader.Module):
    """Advanced settings for GeekTG only"""

    strings = {
        "name": "AdvancedSettings",
        "watchers": "👾 <b>Watchers:</b>\n\n<b>{}</b>",
        "mod404": "👾 <b>Watcher {} not found</b>",
        "already_disabled": "👾 <b>Watcher {} already disabled</b>",
        "disabled": "👾 <b>Watcher {} is now disabled</b>",
        "enabled": "👾 <b>Watcher {} is now enabled</b>",
        "args": "👾 <b>You need to specify watcher name</b>",
        "user_nn": "🔰 <b>NoNick for this user is now {}</b>",
        "no_cmd": "🔰 <b>Please, specify command to toggle NoNick for</b>",
        "cmd_nn": "🔰 <b>NoNick for </b><code>{}</code><b> is now {}</b>",
        "cmd404": "🔰 <b>Command not found</b>",
    }

    def get_watchers(self) -> tuple:
        return [
            str(_.__self__.__class__.strings["name"])
            for _ in self.allmodules.watchers
            if _.__self__.__class__.strings is not None
        ], self._db.get(main.__name__, "disabled_watchers", {})

    async def client_ready(self, client, db) -> None:
        self._db = db
        self._client = client

    async def watcherscmd(self, message: Message) -> None:
        """List current watchers"""
        watchers, disabled_watchers = self.get_watchers()
        watchers = [
            f"♻️ {_}" for _ in watchers if _ not in list(disabled_watchers.keys())
        ]
        watchers += [f"💢 {k} {v}" for k, v in disabled_watchers.items()]
        await utils.answer(
            message, self.strings("watchers").format("\n".join(watchers))
        )

    async def watcherblcmd(self, message: Message) -> None:
        """<module> - Toggle watcher in current chat"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings("args"))

        watchers, disabled_watchers = self.get_watchers()

        if args.lower() not in [_.lower() for _ in watchers]:
            return await utils.answer(message, self.strings("mod404").format(args))

        args = [_ for _ in watchers if _.lower() == args.lower()][0]

        current_bl = [
            v for k, v in disabled_watchers.items() if k.lower() == args.lower()
        ]
        current_bl = current_bl[0] if current_bl else []

        chat = utils.get_chat_id(message)
        if chat not in current_bl:
            if args in disabled_watchers:
                for k, _ in disabled_watchers.items():
                    if k.lower() == args.lower():
                        disabled_watchers[k].append(chat)
                        break
            else:
                disabled_watchers[args] = [chat]

            await utils.answer(
                message,
                self.strings("disabled").format(args) + " <b>in current chat</b>",
            )
        else:
            for k in disabled_watchers.copy():
                if k.lower() == args.lower():
                    disabled_watchers[k].remove(chat)
                    if not disabled_watchers[k]:
                        del disabled_watchers[k]
                    break

            await utils.answer(
                message,
                self.strings("enabled").format(args) + " <b>in current chat</b>",
            )

        self._db.set(main.__name__, "disabled_watchers", disabled_watchers)

    async def watchercmd(self, message: Message) -> None:
        """<module> - Toggle global watcher rules
        Args:
        [-c - only in chats]
        [-p - only in pm]
        [-o - only out]
        [-i - only incoming]"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings("args"))

        chats, pm, out, incoming = False, False, False, False

        if "-c" in args:
            args = args.replace("-c", "").replace("  ", " ").strip()
            chats = True

        if "-p" in args:
            args = args.replace("-p", "").replace("  ", " ").strip()
            pm = True

        if "-o" in args:
            args = args.replace("-o", "").replace("  ", " ").strip()
            out = True

        if "-i" in args:
            args = args.replace("-i", "").replace("  ", " ").strip()
            incoming = True

        if chats and pm:
            pm = False
        if out and incoming:
            incoming = False

        watchers, disabled_watchers = self.get_watchers()

        if args.lower() not in [_.lower() for _ in watchers]:
            return await utils.answer(message, self.strings("mod404").format(args))

        args = [_ for _ in watchers if _.lower() == args.lower()][0]

        if chats or pm or out or incoming:
            disabled_watchers[args] = [
                *(["only_chats"] if chats else []),
                *(["only_pm"] if pm else []),
                *(["out"] if out else []),
                *(["in"] if incoming else []),
            ]
            self._db.set(main.__name__, "disabled_watchers", disabled_watchers)
            await utils.answer(
                message,
                self.strings("enabled").format(args)
                + f" (<code>{disabled_watchers[args]}</code>)",
            )
            return

        if args in disabled_watchers and "*" in disabled_watchers[args]:
            await utils.answer(message, self.strings("enabled").format(args))
            del disabled_watchers[args]
            self._db.set(main.__name__, "disabled_watchers", disabled_watchers)
            return

        disabled_watchers[args] = ["*"]
        self._db.set(main.__name__, "disabled_watchers", disabled_watchers)
        await utils.answer(message, self.strings("disabled").format(args))

    async def nonickusercmd(self, message: Message) -> None:
        """Allow certain command to be executed without nickname"""
        reply = await message.get_reply_message()
        u = reply.sender_id
        if not isinstance(u, int):
            u = u.user_id

        nn = self._db.get(main.__name__, "nonickusers", [])
        if u not in nn:
            nn += [u]
            nn = list(set(nn))  # skipcq: PTC-W0018
            await utils.answer(message, self.strings("user_nn").format("on"))
        else:
            nn = list(set(nn) - set([u]))  # skipcq: PTC-W0018
            await utils.answer(message, self.strings("user_nn").format("off"))

        self._db.set(main.__name__, "nonickusers", nn)

    async def nonickcmdcmd(self, message: Message) -> None:
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings("no_cmd"))

        if args not in self.allmodules.commands:
            return await utils.answer(message, self.strings("cmd404"))

        nn = self._db.get(main.__name__, "nonickcmds", [])
        if args not in nn:
            nn += [args]
            nn = list(set(nn))
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    self._db.get(main.__name__, "command_prefix", ["."])[0] + args, "on"
                ),
            )
        else:
            nn = list(set(nn) - set([args]))  # skipcq: PTC-W0018
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    self._db.get(main.__name__, "command_prefix", ["."])[0] + args, "off"
                ),
            )

        self._db.set(main.__name__, "nonickcmds", nn)
