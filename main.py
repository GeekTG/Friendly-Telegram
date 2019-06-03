import logging, os, sys, argparse, asyncio
#logging.basicConfig(level=logging.ERROR, datefmt='')

from telethon import TelegramClient, sync, events

from . import loader, __main__

# Not public.
modules = loader.Modules.get()

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

async def handle_incoming(event):
    logging.debug("Incoming message!")
    message = event.message
    logging.debug(message)
    for fun in modules.watchers:
        await fun(message)

def run_config():
    from . import configurator
    configurator.main()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", "-s", action="store_true")
    parser.add_argument("--config", "-c", action="append")
    parser.add_argument("--value", "-v", action="append")
    arguments = parser.parse_args()
    logging.debug(arguments)

    if arguments.setup:
        run_config()
        return

    try:
        from . import config
    except:
        run_config()
        return

    cfg = arguments.config if arguments.config else []
    vlu = arguments.value if arguments.value else []

    from . import api_token
    # Do this early on so we can register listeners
    client = TelegramClient('friendly-telegram', api_token.ID, api_token.HASH).start()
    # Stop modules taking personal data so easily, or by accident
    del api_token.ID
    del api_token.HASH

    client.on(events.NewMessage(incoming=True, forwards=False))(handle_incoming)
    client.on(events.NewMessage(outgoing=True, forwards=False, pattern=r'\..*'))(handle_command)

    modules.register_all()

    modules.send_config(dict(zip(cfg, vlu)))

    asyncio.get_event_loop().set_exception_handler(lambda _, x: logging.error("Exception on event loop! %s", x["message"], exc_info=x["exception"]))
    asyncio.get_event_loop().run_until_complete(amain(client))

async def amain(client):
    async with client as c:
        await c.start()
        await modules.send_ready(client)
        await c.run_until_disconnected()
