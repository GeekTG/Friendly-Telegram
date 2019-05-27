from .. import loader, main
import logging
from telethon import functions

def register(cb):
    logging.debug('Registering %s', __file__)
    cb(PurgeMod())

class PurgeMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'purge':self.purgecmd}
        self.config = {}
        self.name = "Purge"
        self.help = "Deletes things quickly"

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
