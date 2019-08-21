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

import logging

from .. import loader, utils

logger = logging.getLogger(__name__)

def register(cb):
    cb(ForwardMod())

class ForwardMod(loader.Module):
    """Forwards messages"""
    def __init__(self):
        self.name = _("Forwarding")

    async def fwdallcmd(self, message):
        """.fwdall <to_user>
           Forwards all messages in chat"""
        user = utils.get_args(message)[0]
        msgs = []
        async for msg in message.client.iter_messages(
                entity=message.to_id,
                reverse=True):
            msgs += [msg.id]
            if len(msgs) >= 100:
                logger.debug(msgs)
                await message.client.forward_messages(user, msgs, message.from_id)
                msgs = []
            # No async list comprehension in 3.5
        if len(msgs) > 0:
            logger.debug(msgs)
            await message.client.forward_messages(user, msgs, message.from_id)

