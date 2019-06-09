# -*- coding: future_fstrings -*-

from .. import loader, utils
import logging, warnings, functools, asyncio, itertools, re
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

def register(cb):
    cb(StickersMod())

#                             normal emojis        emoji mod  join mod
RE_EMOJI = re.compile('(?:[\U00010000-\U0010ffff]|(?:.\ufe0f)|\u200d|\u20e3)*', flags=re.UNICODE)

def is_just_emoji(string):
    r = RE_EMOJI.fullmatch(string)
    logger.debug(ascii(r))
    logger.debug(RE_EMOJI)
    return r != None

class StickersMod(loader.Module):
    """Tasks with stickers"""
    def __init__(self):
        logger.debug('%s started', __file__)
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        self.commands = {'kang':self.kangcmd}
        self.config = {"STICKERS_USERNAME":"Stickers", "STICKER_SIZE":(512, 512), "DEFAULT_STICKER_EMOJI":u"🤔"}
        self.name = "Stickers"

    async def kangcmd(self, message):
        """Use in reply or with an attached media:
           .kang <pack name> [emojis]
           If pack is not matched the most recent will be used instead"""
        args = utils.get_args(message)
        if (len(args) != 1 and len(args) != 2) or (len(args) == 2 and not is_just_emoji(args[1].strip())):
            logger.debug("wrong args len(%s) or bad(%s) emoji(%s) args(%s)", len(args), is_just_emoji(args[1].strip()), ascii(args[1].strip()), args)
            await message.edit("Provide a pack name and optionally emojis too")
            return

        if not message.is_reply:
            if message.sticker or message.photo:
                logger.debug("user sent photo/sticker directly not reply")
                sticker = message
            else:
                logger.debug("user didnt send any sticker/photo or reply")
                await message.edit("Reply to a sticker or photo to nick it")
                return
        else:
            sticker = await message.get_reply_message()
        if not (sticker.sticker or sticker.photo):
            await message.edit("That ain't no photo")
            return
        logger.debug("user did send photo/sticker")
        try:
            img = BytesIO()
            await sticker.download_media(file=img)
            logger.debug(img)
            try:
                thumb = BytesIO()
                await asyncio.get_event_loop().run_in_executor(None, functools.partial(resize_image, img, self.config["STICKER_SIZE"], thumb))
                img.close()
                thumb.name = "sticker.png"
                thumb.seek(0)
                # The data is now in thumb.
                if len(args) > 1:
                    emojis = args[1]
                elif sticker.sticker:
                    emojis = sticker.file.emoji
                else:
                    emojis = self.config["DEFAULT_STICKER_EMOJI"]
                logger.debug(emojis)
                # Without t.me/ there is ambiguity; Stickers could be a name, in which case the wrong entity could be returned
                conv = message.client.conversation("t.me/"+self.config["STICKERS_USERNAME"], timeout=5, exclusive=True)
                async with conv:
                    first = await conv.send_message("/cancel")
                    await conv.send_message("/addsticker")
                    buttons = (await conv.get_response()).buttons
                    if buttons != None:
                        logger.debug("there are buttons, good")
                        button = click_buttons(buttons, args[0])
                        await button.click()
                    else:
                        logger.warning("there's no buttons!")
                        await message.client.send_message("t.me/"+self.config["STICKERS_USERNAME"], "/cancel")
                        await message.edit("Something went wrong")
                        return
                    # We have sent the pack we wish to modify.
                    # Upload sticker
                    # No need to wait for response, the bot doesn't care.
                    m = await conv.send_file(thumb, force_document=True)
                    await conv.send_message(emojis)
                    await conv.send_message("/done")
                    # Block now so that we mark it all as read
                    await conv.get_response()
                    r = await conv.get_response(m)
                    if "512" in r.message:
                        # That's an error:
                        # Sorry, the image dimensions are invalid. Please check that the image fits into a 512x512 square (one of the sides should be 512px and the other 512px or less).
                        logger.error("Bad response from StickerBot")
                        logger.error(r)
                        await message.edit("<code>Something went wrong internally!</code>", parse_mode="HTML")
                        return
                await message.client.send_read_acknowledge(conv.chat_id)

                msgs = []
                async for msg in message.client.iter_messages(
                        entity="t.me/"+self.config["STICKERS_USERNAME"],
                        min_id=first.id,
                        reverse=True):
                    msgs += [msg.id]
                logger.debug(msgs)
                await message.client.delete_messages("t.me/"+self.config["STICKERS_USERNAME"], msgs+[first])
#                await message.client.send_message("t.me/"+self.config["STICKERS_USERNAME"], "/cancel")
            finally:
                thumb.close()
        finally:
            img.close()
        packurl = utils.escape_quotes(f"https://t.me/addstickers/{button.text}")
        await message.edit(f'<code>Sticker added to</code> <a href="{packurl}">pack</a><code>!</code>', parse_mode="HTML")

def click_buttons(buttons, target_pack):
    buttons = list(itertools.chain.from_iterable(buttons))
    # Process in reverse order; most difficult to match first
    try:
        return buttons[int(target_pack)]
    except:
        pass
    logger.debug(buttons)
    for button in buttons:
        logger.debug(button)
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
    try:
        im = Image.open(img)
        # We used to use thumbnail(size) here, but it returns with a *max* dimension of 512,512 rather than making one side exactly 512
        # So we have to calculate dimensions manually :(
        if im.width == im.height:
            size = (512, 512)
        elif im.width < im.height:
            size = (int(512*im.width/im.height), 512)
        else:
            size = (512, int(512*im.height/im.width))
        logger.debug("Resizing to %s", size)
        im.resize(size).save(dest, "PNG")
    finally:
        del im
