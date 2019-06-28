# -*- coding: future_fstrings -*-

import logging

from .. import loader, utils

logger = logging.getLogger(__name__)

def register(cb):
    cb(ForwardMod())

class ForwardMod(loader.Module):
    """Forwards messages"""
    def __init__(self):
        self.commands = {"fwdall":self.fwdallcmd}
        self.config = {}
        self.name = "Forwarding"

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

