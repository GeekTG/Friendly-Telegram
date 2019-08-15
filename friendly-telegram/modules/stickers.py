# -*- coding: future_fstrings -*-

#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .. import loader, utils
import logging, warnings, itertools, asyncio
from io import BytesIO
from PIL import Image
import tgs

logger = logging.getLogger(__name__)

warnings.simplefilter('error', Image.DecompressionBombWarning)


def register(cb):
    cb(StickersMod())

class StickersMod(loader.Module):
    """Tasks with stickers"""
    def __init__(self):
        self.config = {"STICKERS_USERNAME":"Stickers", "STICKER_SIZE":(512, 512), "DEFAULT_STICKER_EMOJI":u"🤔"}
        self.name = "Stickers"
        self._lock = asyncio.Lock()

    async def kangcmd(self, message):
        """Use in reply or with an attached media:
           .kang <pack name> [emojis]
           If pack is not matched the most recently created will be used instead"""
        args = utils.get_args(message)
        if len(args) != 1 and len(args) != 2:
            logger.debug("wrong args len(%s) or bad args(%s)", len(args), args)
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
            img.seek(0)
            logger.debug(img)
            try:
                thumb = BytesIO()
                await utils.run_sync(resize_image, img, self.config["STICKER_SIZE"], thumb)
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
                # Lock access to @Stickers
                async with self._lock:
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
                        m1 = await conv.send_file(thumb, force_document=True)
                        m2 = await conv.send_message(emojis)
                        await conv.send_message("/done")
                        # Block now so that we mark it all as read
                        await conv.get_response()
                        await message.client.send_read_acknowledge(conv.chat_id)
                        r1 = await conv.get_response(m1)
                        if "512" in r1.message:
                            # That's an error:
                            # Sorry, the image dimensions are invalid. Please check that the image fits into a 512x512 square (one of the sides should be 512px and the other 512px or less).
                            logger.error("Bad response from StickerBot 1")
                            logger.error(r1)
                            await message.edit("<code>Something went wrong internally!</code>")
                            return
                        r2 = await conv.get_response(m2)
                        msgs = []
                        async for msg in message.client.iter_messages(
                            entity="t.me/"+self.config["STICKERS_USERNAME"],
                            min_id=first.id,
                            reverse=True):
                            msgs += [msg.id]
                    logger.debug(msgs)
                    await message.client.delete_messages("t.me/"+self.config["STICKERS_USERNAME"], msgs+[first])
                    if "emoji" in r2.message:
                        # The emoji(s) are invalid.
                        logger.error("Bad response from StickerBot 2")
                        logger.error(r2)
                        await message.edit("<code>Please provide valid emoji(s).</code>")
                        return
            finally:
                thumb.close()
        finally:
            img.close()
        packurl = utils.escape_quotes(f"https://t.me/addstickers/{button.text}")
        await message.edit(f'<code>Sticker added to</code> <a href="{packurl}">pack</a><code>!</code>')

    async def gififycmd(self, message):
        """Convert the replied animated sticker to a GIF"""
        target = await message.get_reply_message()
        if target is None or target.file is None or target.file.mime_type != 'application/x-tgsticker':
            await utils.answer(message, "<code>Please provide an animated sticker to convert to a GIF</code>")
        try:
            file = BytesIO()
            await target.download_media(file)
            file.seek(0)
            anim = await utils.run_sync(tgs.parsers.tgs.parse_tgs, file)
            file.close()
            result = BytesIO()
            result.name = "animation.gif"
            tgs.exporters.gif.export_gif(anim, result, 256, 5)
            result.seek(0)
            await utils.answer(message, result)
        finally:
            try:
                file.close()
            except:
                pass
            try:
                result.close()
            except:
                pass

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
