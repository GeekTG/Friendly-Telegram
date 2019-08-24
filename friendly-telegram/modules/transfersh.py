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

import logging
import requests
import asyncio

from .. import loader, utils

logger = logging.getLogger(__name__)


def register(cb):
    cb(TransferShMod())


def sgen(agen, loop):
    while True:
        try:
            yield utils.run_async(loop, agen.__anext__())
        except StopAsyncIteration:
            return


class TransferShMod(loader.Module):
    """Upload to and from transfer.sh"""
    def __init__(self):
        self.config = {"UPLOAD_URL": "https://transfer.sh/{}"}
        self.name = _("transfer.sh support")

    async def uploadshcmd(self, message):
        """Uploads to transfer.sh"""
        if message.file:
            msg = message
        else:
            msg = (await message.get_reply_message())
        doc = msg.media
        if doc is None:
            await message.edit(_("<code>Provide a file to upload</code>"))
            return
        doc = message.client.iter_download(doc)
        logger.debug("begin transfer")
        await message.edit(_("<code>Uploading...</code>"))
        r = await utils.run_sync(requests.put, self.config["UPLOAD_URL"].format(msg.file.name),
                                 data=sgen(doc, asyncio.get_event_loop()))
        logger.debug(r)
        r.raise_for_status()
        logger.debug(r.headers)
        await message.edit(_("<a href={}>Uploaded!</a>").format(r.text))

# This code doesn't work.
#    async def downloadshcmd(self, message):
#        """Downloads from transfer.sh"""
#        args = utils.get_args(message)
#        if len(args) < 1:
#            await message.edit("<code>Provide a link to download</code>")
#            return
#        url = args[0]
#        if url.startswith("http://"):
#            url = message.message.replace("http://", "https://", 1)
#        elif not url.startswith("https://"):
#            url = "https://" + url
#        if url.startswith("https://transfer.sh/"):
#            url = url.replace("https://transfer.sh/", "https://transfer.sh/get/", 1)
#        logger.error(url)
#        await utils.answer(message, url, asfile=True)
