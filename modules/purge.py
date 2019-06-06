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
        msgs = [msg.id async for msg in message.client.iter_messages(
            entity=message.to_id,
            min_id=message.reply_to_msg_id,
            reverse=True
        )]
        logger.debug(msgs)
        await message.client.delete_messages(message.to_id, msgs+[message.reply_to_msg_id])

    async def delcmd(self, message):
        """Delete the replied message"""
        await message.delete()
        if not message.is_reply:
            iter = message.client.iter_messages(
                entity=message.to_id
            )
            await (await iter.__anext__()).delete()
        else:
            await (await message.get_reply_message()).delete()
