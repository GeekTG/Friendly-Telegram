"""
    █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
    █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█

    Copyright 2022 t.me/hikariatama
    Licensed under the GNU GPLv3
"""

# <3 title: GeekSecurity
# <3 pic: https://img.icons8.com/stickers/100/000000/enter-pin.png
# <3 desc: Control security settings (geek3.0.8alpha+)

# scope: inline_content

from types import FunctionType
from typing import Union, List
from telethon.tl.types import Message

from .. import loader, utils, main, security
import logging
import aiogram
from ..security import \
    OWNER, \
    SUDO, \
    SUPPORT, \
    GROUP_OWNER, \
    GROUP_ADMIN_ADD_ADMINS, \
    GROUP_ADMIN_CHANGE_INFO, \
    GROUP_ADMIN_BAN_USERS, \
    GROUP_ADMIN_DELETE_MESSAGES, \
    GROUP_ADMIN_PIN_MESSAGES, \
    GROUP_ADMIN_INVITE_USERS, \
    GROUP_ADMIN, \
    GROUP_MEMBER, \
    PM, \
    DEFAULT_PERMISSIONS

logger = logging.getLogger(__name__)


def chunks(lst: list, n: int) -> List[list]:
    return [lst[i:i + n] for i in range(0, len(lst), n)]


@loader.tds
class GeekSecurityMod(loader.Module):
    """Control security settings (geek3.0.8alpha+)"""
    strings = {
        "name": "GeekSecurity",
        "no_command": "🚫 <b>Command </b><code>{}</code><b> not found!</b>",
        "permissions": "🔐 <b>Here you can configure permissions for </b><code>{}{}</code>",
        "close_menu": '🙈 Close this menu',
        "global": "🔐 <b>Here you can configure global bounding mask. If the permission is excluded here, it is excluded everywhere!</b>",

        'owner': "🤴 Owner",
        'sudo': "🤵 Sudo",
        'support': "💁‍♂️ Support",
        'group_owner': "🧛‍♂️ Group owner",
        'group_admin_add_admins': "👨‍💻 Admin (add members)",
        'group_admin_change_info': "👨‍💻 Admin (change info)",
        'group_admin_ban_users': "👨‍💻 Admin (ban)",
        'group_admin_delete_messages': "👨‍💻 Admin (delete msgs)",
        'group_admin_pin_messages': "👨‍💻 Admin (pin)",
        'group_admin_invite_users': "👨‍💻 Admin (invite)",
        'group_admin': "👨‍💻 Admin (any)",
        'group_member': "👥 In group",
        'pm': "🤙 In PM"
    }

    def get(self, *args) -> dict:
        return self.db.get(self.strings['name'], *args)

    def set(self, *args) -> None:
        return self.db.set(self.strings['name'], *args)

    async def client_ready(self, client, db) -> None:
        self.db = db
        self.client = client
        self.prefix = utils.escape_html(
            (
                self.db.get(
                    main.__name__,
                    "command_prefix",
                    False
                ) or ".")[0]
        )

    async def inline__switch_perm(self, call: aiogram.types.CallbackQuery, command: str, group: str, level: bool) -> None:
        cmd = self.allmodules.commands[command]
        mask = self.db.get(
            security.__name__, "masks", {}
        ) \
            .get(
            cmd.__module__ + "." + cmd.__name__,
            getattr(
                cmd,
                "security",
                security.DEFAULT_PERMISSIONS
            )
        )

        bit = security.BITMAP[group.upper()]

        if level:
            mask |= bit
        else:
            mask &= ~bit

        masks = self.db.get(security.__name__, "masks", {})
        masks[cmd.__module__ + "." + cmd.__name__] = mask
        self.db.set(security.__name__, "masks", masks)

        await call.answer('Security value set!')
        await call.edit(
            self.strings('permissions')
            .format(
                self.prefix,
                command
            ),
            reply_markup=self._build_markup(cmd)
        )

    async def inline__switch_perm_bm(self, call: aiogram.types.CallbackQuery, group: str, level: bool) -> None:
        mask = self.db.get(security.__name__,
                           "bounding_mask", DEFAULT_PERMISSIONS)
        bit = security.BITMAP[group.upper()]

        if level:
            mask |= bit
        else:
            mask &= ~bit

        self.db.set(security.__name__, "bounding_mask", mask)

        await call.answer('Bounding mask value set!')
        await call.edit(
            self.strings('global'),
            reply_markup=self._build_markup_global()
        )

    async def inline_close(self, call: aiogram.types.CallbackQuery) -> None:
        await call.delete()

    def _build_markup(self, command: FunctionType) -> List[List[dict]]:
        perms = self._get_current_perms(command)
        buttons = [
            {
                'text': ('🚫' if not level else '✅') + ' ' +
                self.strings[group],
                'callback': self.inline__switch_perm,
                'args': (command.__name__[:3], group, not level)
            }
            for group, level in perms.items()
        ]

        return chunks(buttons, 2) + [[{
            'text': self.strings('close_menu'),
            'callback': self.inline_close
        }]]

    def _build_markup_global(self) -> List[List[dict]]:
        perms = self._get_current_bm()
        buttons = [
            {
                'text': ('🚫' if not level else '✅') + ' ' +
                self.strings[group],
                'callback': self.inline__switch_perm_bm,
                'args': (group, not level)
            }
            for group, level in perms.items()
        ]

        return chunks(buttons, 2) + [[{
            'text': self.strings('close_menu'),
            'callback': self.inline_close
        }]]

    def _get_current_bm(self) -> dict:
        return self._perms_map(self.db.get(security.__name__, "bounding_mask", DEFAULT_PERMISSIONS))

    def _perms_map(self, perms: int) -> dict:
        return {
            'owner': bool(perms & OWNER),
            'sudo': bool(perms & SUDO),
            'support': bool(perms & SUPPORT),
            'group_owner': bool(perms & GROUP_OWNER),
            'group_admin_add_admins': bool(perms & GROUP_ADMIN_ADD_ADMINS),
            'group_admin_change_info': bool(perms & GROUP_ADMIN_CHANGE_INFO),
            'group_admin_ban_users': bool(perms & GROUP_ADMIN_BAN_USERS),
            'group_admin_delete_messages': bool(perms & GROUP_ADMIN_DELETE_MESSAGES),
            'group_admin_pin_messages': bool(perms & GROUP_ADMIN_PIN_MESSAGES),
            'group_admin_invite_users': bool(perms & GROUP_ADMIN_INVITE_USERS),
            'group_admin': bool(perms & GROUP_ADMIN),
            'group_member': bool(perms & GROUP_MEMBER),
            'pm': bool(perms & PM)
        }

    def _get_current_perms(self, command: FunctionType) -> dict:
        config = loader.dispatcher.security.get_flags(command)

        return self._perms_map(config)

    async def securitycmd(self, message: Message) -> None:
        """[command] - Configure command's security settings"""
        args = utils.get_args_raw(message).lower().strip()
        if args and args not in self.allmodules.commands:
            await utils.answer(message, self.strings('no_command').format(args))
            return

        if not args:
            await self.inline.form(
                self.strings('global'),
                reply_markup=self._build_markup_global(),
                message=message,
                ttl=5 * 60
            )
            return  # TODO: Global permissions

        cmd = self.allmodules.commands[args]

        await self.inline.form(
            self.strings('permissions').format(self.prefix, args),
            reply_markup=self._build_markup(cmd),
            message=message,
            ttl=5 * 60
        )
