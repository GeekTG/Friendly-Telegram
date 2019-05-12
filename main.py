import logging
logging.basicConfig(level=logging.DEBUG, datefmt='')

from telethon import TelegramClient, sync, events

from . import api_token
client = TelegramClient('friendly-telegram', api_token.ID, api_token.HASH).start()

del api_token.ID
del api_token.HASH

from . import loader
modules = loader.Modules.get()
modules.register_all()

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
    with client:
        client.start()
        client.run_until_disconnected()
