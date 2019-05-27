import logging, os, sys, argparse, asyncio
logging.basicConfig(level=logging.DEBUG, datefmt='')

from telethon import TelegramClient, sync, events

from . import api_token
client = TelegramClient('friendly-telegram', api_token.ID, api_token.HASH).start()
del api_token.ID
del api_token.HASH

from . import loader, __main__

modules = loader.Modules.get()
modules.register_all()

parser = argparse.ArgumentParser()
parser.add_argument("--config", "-c", action="append")
parser.add_argument("--value", "-v", action="append")
arguments = parser.parse_args()
logging.debug(arguments)
cfg = arguments.config if arguments.config else []
vlu = arguments.value if arguments.value else []
logging.debug(str(dict(zip(cfg, vlu))))
modules.send_config(dict(zip(cfg, vlu)))

@client.on(events.NewMessage(outgoing=True, forwards=False, pattern=r'\..*'))
async def handle_command(event):
    logging.debug("Incoming command!")
    if not event.message:
        logging.debug("Ignoring command with no text.")
        return
    if event.via_bot_id:
        logging.debug("Ignoring inline bot.")
        return
    message = event.message
    logging.debug(message)
    command = message.message.split(' ',1)[0]
    try:
        params = message.message.split(' ',1)[1]
    except IndexError:
        params = ""
    logging.debug(command)
    await modules.dispatch(command, message) # modules.dispatch is not a coro, but returns one

@client.on(events.NewMessage(incoming=True, forwards=False))
async def handle_incoming(event):
    logging.debug("Incoming message!")
    message = event.message
    logging.debug(message)
    for fun in modules.watchers:
        await fun(message)

def main():
    asyncio.get_event_loop().run_until_complete(amain())

async def amain():
    async with client as c:
        await c.start()
        await modules.send_ready()
        await c.run_until_disconnected()
