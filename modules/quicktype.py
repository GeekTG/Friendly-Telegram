from .. import loader, utils
import logging, asyncio

def register(cb):
    logging.debug('registering %s', __file__)
    cb(QuickTypeMod())

class QuickTypeMod(loader.Module):
    """Deletes your message after a timeout"""
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'quicktype':self.typecmd}
        self.config = {}
        self.name = "Quick Typer"

    async def typecmd(self, message):
        """.quicktype <timeout> <message>"""
        args = utils.get_args(message)
        logging.debug(args)
        if len(args) == 0:
            await message.edit("U wot? I need something to type")
            return
        if len(args) == 1:
            await message.edit("Go type it urself m8")
            return
        t = args[0]
        mess = ' '.join(args[1:])
        try:
            t = float(t)
        except ValueError:
            await message.edit("Nice number bro")
            return
        await message.delete()
        m = await message.client.send_message(message.to_id, str(mess))
        await asyncio.sleep(t)
        await m.delete()
