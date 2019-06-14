# -*- coding: future_fstrings -*-

import logging

from .. import loader, main, utils

def register(cb):
    cb(CoreMod())

class CoreMod(loader.Module):
    """Control core userbot settings"""
    def __init__(self):
        self.commands = {'blacklist':self.blacklistcmd, "unblacklist":self.unblacklistcmd, "whitelist":self.whitelistcmd, "unwhitelist":self.unwhitelistcmd}
        self.config = {}
        self.name = "Settings"

    async def client_ready(self, client, db):
        self._db = db

    async def blacklistcommon(self, message):
        args = utils.get_args(message)
        if len(args) > 1:
            await message.edit("<code>Too many args</code>")
            return
        id = None
        if len(args) == 1:
            try:
                id = int(args[0])
            except ValueError:
                pass
        if id is None:
            id = utils.get_chat_id(message)
        return id

    async def blacklistcmd(self, message):
        """.blacklist [id]
           Blacklist the bot from operating somewhere"""
        id = await self.blacklistcommon(message)
        self._db.set(main.__name__, "blacklist_chats", self._db.get(main.__name__, "blacklist_chats", [])+[id])
        await message.edit(f"<code>Chat {id} blacklisted from userbot</code>")

    async def unblacklistcmd(self, message):
        """.unblacklist [id]
           Unblacklist the bot from operating somewhere"""
        id = await self.blacklistcommon(message)
        self._db.set(main.__name__, "blacklist_chats", list(set(self._db.get(main.__name__, "blacklist_chats", []))-set([id])))
        await message.edit(f"<code>Chat {id} unblacklisted from userbot</code>")

    async def whitelistcmd(self, message):
        """.whitelist [id]
           Whitelist the bot from operating somewhere"""
        id = await self.blacklistcommon(message)
        self._db.set(main.__name__, "whitelist_chats", self._db.get(main.__name__, "whitelist_chats", [])+[id])
        await message.edit(f"<code>Chat {id} whitelisted from userbot</code>")

    async def unwhitelistcmd(self, message):
        """.unwhitelist [id]
           Unwhitelist the bot from operating somewhere"""
        id = await self.blacklistcommon(message)
        self._db.set(main.__name__, "whitelist_chats", list(set(self._db.get(main.__name__, "whitelist_chats", []))-set([id])))
        await message.edit(f"<code>Chat {id} unwhitelisted from userbot</code>")

