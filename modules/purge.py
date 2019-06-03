from .. import loader
import logging

def register(cb):
    logging.debug('Registering %s', __file__)
    cb(PurgeMod())

class PurgeMod(loader.Module):
    """Deletes your messages"""
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'purge':self.purgecmd, "del":self.delcmd}
        self.config = {}
        self.name = "Purge"

    async def purgecmd(self, message):
        if not message.is_reply:
            await message.edit("From where shall I purge?")
            return
        msgs = [msg.id async for msg in message.client.iter_messages(
            entity=message.to_id,
            min_id=message.reply_to_msg_id,
            reverse=True
        )]
        await message.client.delete_messages(message.to_id, msgs+[message.reply_to_msg_id])

    async def delcmd(self, message):
        await message.delete()
        if not message.is_reply:
            iter = message.client.iter_messages(
                entity=message.to_id
            )
            await (await iter.__anext__()).delete()
        else:
            await (await message.get_reply_message()).delete()
