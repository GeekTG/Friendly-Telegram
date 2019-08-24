# -*- coding: future_fstrings -*-

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

import telethon

from .. import loader, utils


def register(cb):
    cb(RecentActionsMod())


class RecentActionsMod(loader.Module):
    """Reads recent actions"""
    def __init__(self):
        self.name = _("Recent Actions")

    async def recoverdeletedcmd(self, message):
        """Restores deleted messages sent after replied message (optionally specify how many to recover)"""
        msgs = message.client.iter_admin_log(message.to_id, delete=True)
        if not message.is_reply:
            await utils.answer(message, _("<code>Reply to a message to specify where to start</code>"))
            return
        target = (await message.get_reply_message()).date
        ret = []
        try:
            async for msg in msgs:
                if msg.original.date < target:
                    break
                if msg.original.action.message.date < target:
                    continue
                ret += [msg]
        except telethon.errors.rpcerrorlist.ChatAdminRequiredError:
            await utils.answer(message, _("<code>Admin is required to read deleted messages</code>"))
        args = utils.get_args(message)
        if len(args) > 0:
            try:
                count = int(args[0])
                ret = ret[-count:]
            except ValueError:
                pass
        for msg in reversed(ret):
            orig = msg.original.action.message
            deldate = msg.original.date.isoformat()
            origdate = orig.date.isoformat()
            await message.respond(_("Deleted message {} recovered. Originally sent at {} by {}, deleted at {} by {}")
                                  .format(msg.id, origdate, orig.from_id, deldate, msg.user_id))
            await message.respond(orig)
