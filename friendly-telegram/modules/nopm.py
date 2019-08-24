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

from .. import loader, utils

import logging

from telethon import functions, types

logger = logging.getLogger(__name__)


def register(cb):
    cb(AntiPMMod())


class AntiPMMod(loader.Module):
    """Provides a message saying that you are unavailable (out of office)"""
    def __init__(self):
        self.name = _("Anti PM")
        self._me = None
        self._ratelimit = []

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._me = await client.get_me()

    async def allowcmd(self, message):
        """Allow this user to PM without being warned"""
        if message.is_reply:
            user = (await message.get_reply_message()).from_id
        else:
            user = getattr(message.to_id, "user_id", None)
        if not user:
            await message.edit(_("<code>Who shall I allow to PM?</code>"))
            return
        self._db.set(__name__, "allow", self._db.get(__name__, "allow", []) + [user])
        await message.edit(_("<code>PM Authorised</code>"))

    async def reportcmd(self, message):
        """Report the user spam. Use only in PM"""
        old = self._db.get(__name__, "allow", [])
        try:
            old.remove(getattr(message.to_id, "user_id", None))
            self._db.set(__name__, "allow", old)
        except ValueError:
            pass
        if message.is_reply:
            # Report the message
            await message.client(functions.messages.ReportRequest(peer=await message.client
                                                                  .get_input_entity(message.to_id),
                                                                  ids=[message.reply_to_msg_id],
                                                                  reason=types.InputReportReasonSpam()))
        else:
            await message.client(functions.account.ReportPeerRequest(peer=await message.client
                                                                     .get_input_entity(message.to_id),
                                                                     reason=types.InputReportReasonSpam()))
        await message.edit("<code>You just got reported spam!</code>")

    async def watcher(self, message):
        if getattr(message.to_id, 'user_id', None) == self._me.id:
            logger.debug("pm'd!")
            if message.from_id in self._ratelimit:
                self._ratelimit.remove(message.from_id)
                return
            else:
                self._ratelimit += [message.from_id]
            user = await utils.get_user(message)
            if user.is_self or user.bot or user.verified:
                logger.debug("User is self, bot or verified.")
                return
            if self.get_allowed(message.from_id):
                logger.debug("Authorised pm detected")
            else:
                await message.respond(_("<code>Please do not PM me. You will get reported spam.</code>"))

    def get_allowed(self, id):
        return id in self._db.get(__name__, "allow", [])
