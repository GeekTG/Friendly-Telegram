from .. import loader, utils, main, config
from telethon.errors.rpcerrorlist import *
import logging, time

def register(cb):
    logging.debug('Registering %s', __file__)
    cb(TyperMod())

class TyperMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'type':self.typecmd}
        self.config = {}
        self.name = "TyperMod"
    async def typecmd(self, message):
        a = utils.get_args_raw(message)
        m = ""
        for c in a:
            m += config.TYPE_CHAR
            message = await update_message(message, m)
            time.sleep(0.04)
            m = m[:-1]+c
            message = await update_message(message, m)
            time.sleep(0.02)

async def update_message(message, m):
    try:
        await message.edit(m)
    except MessageNotModifiedError:
        pass # space doesnt count
    except MessageIdInvalidError: # It's gone!
        try:
            logging.warning("message id invalid")
            message.delete()
        except:
            logging.warning("message gone!") # WTF? It's really not here...
        message = await main.client.send_message(message.to_id, m) # Make a new one.

    return message
