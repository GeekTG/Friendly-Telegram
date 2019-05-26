from .. import loader, main, utils
import logging, asyncio

def register(cb):
    logging.debug('registering %s', __file__)
    cb(SpamMod())

class SpamMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'spam':self.spamcmd}
        self.config = {}
        self.name = "Spammer"
    async def spamcmd(self, message):
        use_reply = False
        args = utils.get_args(message)
        logging.debug(args)
        if len(args) == 0:
            await message.edit("U wot? I need something to spam")
            return
        if len(args) == 1:
            if message.is_reply:
                use_reply = True
            else:
                await message.edit("Go spam urself m8")
                return
        count = args[0]
        spam = ' '.join(args[1:])
        try:
            count = int(count)
        except ValueError:
            await message.edit("Nice number bro")
            return
        if count < 1:
            await message.edit("Haha much spam")
            return
        await message.delete()
        i = 0
        if use_reply:
            reply = await message.get_reply_message()
            logging.debug(reply)
            while i < count:
                await asyncio.gather(*[reply.forward_to(message.to_id) for x in range(min(count, 100))])
                i += 100
        else:
            while i < count:
                await asyncio.gather(*[main.client.send_message(message.to_id, str(spam)) for x in range(min(count, 100))])
                i += 100
