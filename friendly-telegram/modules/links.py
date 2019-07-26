# -*- coding: future_fstrings -*-
# coded this on my phone. dont blame me for bugs
import logging

from .. import loader, utils

from telethon.tl.types import MessageEntityUrl, MessageMediaWebPage, WebPage
from telethon.errors import InviteHashExpiredError, InviteHashInvalidError, MessageNotModifiedError
from telethon.tl.functions.messages import CheckChatInviteRequest

logger = logging.getLogger(__name__)

def register(cb):
    cb(LinksMod())

class LinksMod(loader.Module):
    """Invite link operations"""
    def __init__(self):
        self.commands = {"findlinks":self.linkscmd}
        self.config = {}
        self.name = "Invite Links"

    async def filterlinks(self, links, client, skip):
        l = []
        for link in links:
            if link.media and isinstance(link.media, MessageMediaWebPage) and isinstance(link.media.webpage, WebPage) and link.media.webpage.type == "telegram_megagroup":
                if not link.media.webpage.url in skip:
                    l += [link.media.webpage.url]
                    continue
            if link.entities:
                for ent in link.entities:
                    if not isinstance(ent, MessageEntityUrl):
                        continue
                    text = link.message[ent.offset:ent.offset+ent.length]
                    if text[:8] == "https://":
                        text = text[8:]
                    if text in skip:
                        continue
                    if len(text) == 36 and text[:14] == "t.me/joinchat/":
                        try:
                            pass
#                            Flood wait of 300s per 3 requests
#                            await client(CheckChatInviteRequest(hash=text[14:]))
                        except (InviteHashExpiredError, InviteHashInvalidError):
                            continue
                        logger.debug("link valid!")
                        l += [text]
        return l

    def formatlinks(self, links):
        return "Searching group(s) for invite links. Results will display gradually below.\n" + "\n".join(links)

    async def flatcb(self, message, goodlinks):
        try:
            await message.edit(self.formatlinks(goodlinks))
        except MessageNotModifiedError:
            pass

    async def linkscmd(self, message):
        """Find all telegram groups through non-recursive listing"""
        await message.edit(self.formatlinks([]))
        await self.searchgroup(message.to_id, message, self.flatcb)

    """
    Screw it  i didnt code this properly!
    async def deepsearchcmd(self, message):
        await message.edit(self.formatlinks([])
        logging.debug(await self.deepsearch(message, 3)

    async def deepsearch(self, message, maxdepth, _depth=0):
        if _depth > maxdepth:
            return {}
        links = set()
        links.add(await self.searchgroup(message.to_id, message, lambda: pass))
        await message.edit(self.formatlinks(links))
        ret = {}
        for link in links:
            ret[link] = await self.deepsearch(message, maxdepth, _depth+1)
        return ret
    """

    async def searchgroup(self, groupid, message, cb):
        links = message.client.iter_messages(groupid, None, search='t.me/')
        goodlinks = set()
        async for link in links:
            goodlinks.update(await self.filterlinks([link], message.client, goodlinks))
            if len(goodlinks) % 10 == 0:
                await cb(message, goodlinks)
            logger.debug(links)
        if len(goodlinks) % 10 != 0:
            await cb(message, goodlinks)
        return goodlinks
