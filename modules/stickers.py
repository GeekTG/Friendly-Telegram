from .. import loader, utils
import logging, warnings, functools, asyncio, emoji, itertools
from io import BytesIO
from PIL import Image

def register(cb):
    logging.debug('Registering %s', __file__)
    cb(StickersMod())

def is_just_emoji(string):
    reg = emoji.get_emoji_regexp()
    off = 0
    while off < len(string):
        r = reg.match(string[off:])
        if not r:
            return False
        off += r.span()[1]
    return True

class StickersMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        self.commands = {'kang':self.kangcmd}
        self.config = {"STICKERS_USERNAME":"Stickers", "STICKER_SIZE":(512, 512), "DEFAULT_STICKER_EMOJI":emoji.emojize("🤔")}
        self.name = "Stickers"
        self.help = "Tasks with stickers"

    async def kangcmd(self, message):
        args = utils.get_args(message)
        if (len(args) != 1 and len(args) != 2) or (len(args) == 2 and not is_just_emoji(args[1])):
            logging.debug("wrong args len or bad emoji args")
            await message.edit("Provide a pack name and optionally emojis too")
            return

        if not message.is_reply:
            if message.sticker or message.photo:
                logging.debug("user sent photo/sticker directly not reply")
                sticker = message
            else:
                logging.debug("user didnt send any sticker/photo or reply")
                await message.edit("Reply to a sticker or photo to nick it")
                return
        else:
            sticker = await message.get_reply_message()
        if not (sticker.sticker or sticker.photo):
            await message.edit("That ain't no photo")
            return
        logging.debug("user did send photo/sticker")
        try:
            img = BytesIO()
            await sticker.download_media(file=img)
            logging.debug(img)
            try:
                thumb = BytesIO()
                await asyncio.get_event_loop().run_in_executor(None, functools.partial(resize_image, img, self.config["STICKER_SIZE"], thumb))
                img.close()
                thumb.name = "sticker.png"
                thumb.seek(0)
                # The data is now in thumb.
                if sticker.sticker:
                    emojis = sticker.file.emoji
                else:
                    emojis = ""
                if len(args) > 1:
                    emojis = args[0]
                if emojis == "":
                    emojis = self.config["DEFAULT_STICKER_EMOJI"]
                # Without t.me/ there is ambiguity; Stickers could be a name, in which case the wrong entity could be returned
                conv = message.client.conversation("t.me/"+self.config["STICKERS_USERNAME"], timeout=5, exclusive=True)
                async with conv:
                    first = await conv.send_message("/cancel")
                    await conv.send_message("/addsticker")
                    buttons = (await conv.get_response()).buttons
                    if buttons != None:
                        logging.debug("there are buttons, good")
                        await click_buttons(buttons, args[0]).click()
                    else:
                        logging.warning("there's no buttons!")
                        await message.edit("Something went wrong")
                        return
                    # We have sent the pack we wish to modify.
                    # Upload sticker
                    # No need to wait for response, the bot doesn't care.
                    await conv.send_file(thumb, force_document=True)
                    await conv.send_message(emojis)
                    await conv.send_message("/done")
                    # Block now so that we mark it all as read
                    await conv.get_response()
                await message.client.send_read_acknowledge(conv.chat_id)

                msgs = [msg.id async for msg in message.client.iter_messages(
                        entity="t.me/"+self.config["STICKERS_USERNAME"],
                        min_id=first.id,
                        reverse=True
                )]
                logging.debug(msgs)
                await message.client.delete_messages("t.me/"+self.config["STICKERS_USERNAME"], msgs+[first])
#                await message.client.send_message("t.me/"+self.config["STICKERS_USERNAME"], "/cancel")
            finally:
                thumb.close()
        finally:
            img.close()

def click_buttons(buttons, target_pack):
    buttons = list(itertools.chain.from_iterable(buttons))
    # Process in reverse order; most difficult to match first
    try:
        return buttons[int(target_pack)]
    except:
        pass
    logging.debug(buttons)
    for button in buttons:
        logging.debug(button)
        if button.text == target_pack:
            return button
    for button in buttons:
        if target_pack in button.text:
            return button
    for button in buttons:
        if target_pack.lower() in button.text.lower():
            return button
    return buttons[-1]

def resize_image(img, size, dest):
    # Wrapper for asyncio purposes
    im = Image.open(img)
    # We don't want to upscale
    im.thumbnail(size)
    im.save(dest, "PNG")

