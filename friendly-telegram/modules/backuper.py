"""
    █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
    █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█

    Copyright 2022 t.me/hikariatama
    Licensed under the GNU GPLv3
"""

# <3 title: Backuper
# <3 pic: https://img.icons8.com/fluency/48/000000/sync-settings.png
# <3 desc: Create the backup of all modules, notes, the whole database

from .. import loader, utils
import asyncio
import datetime
import io
import json

from telethon._tl import Message


@loader.tds
class BackuperMod(loader.Module):
    """Backup everything and anything"""

    strings = {
        "name": "Backuper",
        "backup_caption": "☝️ <b>This is your database backup. Do not give it to anyone, it contains personal info.</b>",
        "reply_to_file": "🚫 <b>Reply to .{} file</b>",
        "db_restored": "🔄 <b>Database updated, restarting...</b>",
        "modules_backup": "🗃 <b>Backup mods ({})</b>",
        "notes_backup": "🗃 <b>Backup notes ({})</b>",
        "mods_restored": "✅ <b>Modes restored, restarting</b>",
        "notes_restored": "✅ <b>Notes restored</b>",
    }

    async def client_ready(self, client, db):
        self.db = db
        self.client = client

    async def backupdbcmd(self, message: Message) -> None:
        """Create database backup [will be sent in pm]"""
        txt = io.BytesIO(json.dumps(self.db).encode("utf-8"))
        txt.name = f"ftg-db-backup-{getattr(datetime, 'datetime', datetime).now().strftime('%d-%m-%Y-%H-%M')}.db"
        await self.client.send_file("me", txt, caption=self.strings("backup_caption"))
        await message.delete()

    async def restoredbcmd(self, message: Message) -> None:
        """Restore database from file"""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            await utils.answer(
                message, self.strings("reply_to_file", message).format("db")
            )
            await asyncio.sleep(3)
            await message.delete()
            return

        file = await message.client.download_file(reply.media)
        decoded_text = json.loads(file.decode("utf-8"))
        self.db.clear()
        self.db.update(**decoded_text)
        self.db.save()
        # print(decoded_text)
        await utils.answer(message, self.strings("db_restored", message))
        await self.allmodules.commands["restart"](await message.respond("_"))

    async def backupmodscmd(self, message: Message) -> None:
        """Create backup of mods"""
        data = json.dumps(
            {
                "loaded": self.db.get(
                    "friendly-telegram.modules.loader", "loaded_modules", []
                ),
                "unloaded": [],
            }
        )
        txt = io.BytesIO(data.encode("utf-8"))
        txt.name = f"ftg-mods-{getattr(datetime, 'datetime', datetime).now().strftime('%d-%m-%Y-%H-%M')}.mods"
        await self.client.send_file(
            utils.get_chat_id(message),
            txt,
            caption=self.strings("modules_backup", message).format(
                len(
                    self.db.get(
                        "friendly-telegram.modules.loader", "loaded_modules", []
                    )
                )
            ),
        )
        await message.delete()

    async def restoremodscmd(self, message: Message) -> None:
        """<reply to file> - Restore mods from backup"""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            await utils.answer(
                message, self.strings("reply_to_file", message).format("mods")
            )
            await asyncio.sleep(3)
            await message.delete()
            return

        file = await message.client.download_file(reply.media)
        decoded_text = json.loads(file.decode("utf-8"))
        self.db.set(
            "friendly-telegram.modules.loader", "loaded_modules", decoded_text["loaded"]
        )
        self.db.set(
            "friendly-telegram.modules.loader",
            "unloaded_modules",
            decoded_text["unloaded"],
        )
        self.db.save()
        await utils.answer(message, self.strings("mods_restored", message))
        await self.allmodules.commands["restart"](await message.respond("_"))

    async def backupnotescmd(self, message: Message) -> None:
        """Create the backup of notes"""
        data = json.dumps(self.db.get("friendly-telegram.modules.notes", "notes", []))
        txt = io.BytesIO(data.encode("utf-8"))
        txt.name = f"ftg-notes-{getattr(datetime, 'datetime', datetime).now().strftime('%d-%m-%Y-%H-%M')}.notes"
        await self.client.send_file(
            utils.get_chat_id(message),
            txt,
            caption=self.strings("notes_backup", message).format(
                len(self.db.get("friendly-telegram.modules.notes", "notes", []))
            ),
        )
        await message.delete()

    async def restorenotescmd(self, message: Message) -> None:
        """<reply to file> - Restore notes from backup"""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            await utils.answer(
                message, self.strings("reply_to_file", message).format("notes")
            )
            await asyncio.sleep(3)
            await message.delete()
            return

        file = await message.client.download_file(reply.media)
        decoded_text = json.loads(file.decode("utf-8"))
        self.db.set("friendly-telegram.modules.notes", "notes", decoded_text)
        self.db.save()
        await utils.answer(message, self.strings("notes_restored", message))
