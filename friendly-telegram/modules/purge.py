from .. import loader
import logging

logger = logging.getLogger(__name__)

def register(cb):
    cb(PurgeMod())

class PurgeMod(loader.Module):
    """Deletes your messages"""
    def __init__(self):
        self.commands = {'purge':self.purgecmd, "del":self.delcmd}
        self.config = {}
        self.name = "Purge"

    async def purgecmd(self, message):
        """Purge from the replied message"""
        if not message.is_reply:
            await message.edit("From where shall I purge?")
            return
        msgs = []
        async for msg in message.client.iter_messages(
                entity=message.to_id,
                min_id=message.reply_to_msg_id,
                reverse=True):
            msgs += [msg.id]
            # No async list comprehension in 3.5
        logger.debug(msgs)
        await message.client.delete_messages(message.to_id, msgs+[message.reply_to_msg_id])

    async def delcmd(self, message):
        """Delete the replied message"""
        msgs = [message.id]
        if not message.is_reply:
            iter = message.client.iter_messages(
                entity=message.to_id
            )
            msgs += [(await iter.__anext__()).id]
        else:
            msgs += [(await message.get_reply_message()).id]
        logger.debug(msgs)
        await message.client.delete_messages(message.to_id, msgs)
