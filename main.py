import logging
logging.basicConfig(level=logging.DEBUG, datefmt='')

from telethon import TelegramClient, sync, events

from . import loader
modules = loader.Modules()
modules.register_all()

from . import api_token
client = TelegramClient('session_name', api_token.ID, api_token.HASH).start()

del api_token.ID
del api_token.HASH

@client.on(events.NewMessage(outgoing=True, forwards=False, pattern=r'\..*'))
async def handle_event(event):
    logging.debug("Incoming event!")
    if not event.message:
        logging.debug("Ignoring event with no text.")
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

def main():
    with client:
        client.start()
        client.run_until_disconnected()
