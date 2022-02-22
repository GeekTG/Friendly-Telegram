"""
    █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
    █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█

    Copyright 2022 t.me/hikariatama
    Licensed under the GNU GPLv3
"""

from .. import loader, utils
import datetime
import io
import json

from telethon.tl.types import *


@loader.tds
class BackuperMod(loader.Module):
    """Backup everything and anything"""
    strings = {
        "name": "Backuper",
        'backup_caption': '☝️ <b>This is your database backup. Don\'t give it to anyone</b>',
        'reply_to_file': '🚫 <b>Reply to .{} file</b>',
        'db_restored': '✅ <b>Database restored. Restarting userbot...</b>',
        'notes_backup': '☝️ <b>Notes backup ({})</b>',
        'notes_restored': '📤 <b>Notes restored.</b>'
    }

    async def client_ready(self, client, db):
        self.db = db
        self.client = client

    async def backupdbcmd(self, message: Message) -> None:
        """Backup database (will be sent in PM)"""
        txt = io.BytesIO(json.dumps(self.db).encode('utf-8'))
        txt.name = f"ftg-db-backup-{datetime.now().strftime('%d-%m-%Y-%H-%M')}.db"
        await self.client.send_file('me', txt, caption=self.strings('backup_caption'))
        await message.delete()

    async def restoredbcmd(self, message: Message) -> None:
        """Restore database from file"""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            await utils.answer(message, self.strings('reply_to_file', message).format('db'))
            return

        file = await message.client.download_file(reply.media)
        decoded_text = json.loads(file.decode('utf-8'))
        self.db.clear()
        self.db.update(**decoded_text)
        self.db.save()
        # print(decoded_text)
        await utils.answer(message, self.strings('db_restored', message))
        await self.allmodules.commands['restart'](await message.respond('_'))

    async def backupnotescmd(self, message: Message) -> None:
        """Backup notes"""
        data = json.dumps(self.db.get(
            "friendly-telegram.modules.notes", "notes", []))
        txt = io.BytesIO(data.encode('utf-8'))
        txt.name = f"ftg-notes-{datetime.now().strftime('%d-%m-%Y-%H-%M')}.notes"
        await self.client.send_file(utils.get_chat_id(message),
                                    txt,
                                    caption=self.strings('notes_backup')
                                    .format(
                                        len(
                                            self.db.get("friendly-telegram.modules.notes",
                                                        "notes",
                                                        []
                                                        )
                                        )
                                    )
        )
        await message.delete()

    async def restorenotescmd(self, message: Message) -> None:
        """<reply to file> - Restore notes from backup"""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            await utils.answer(message, self.strings('reply_to_file', message).format('notes'))
            return

        file = await message.client.download_file(reply.media)
        decoded_text = json.loads(file.decode('utf-8'))
        self.db.set("friendly-telegram.modules.notes", "notes", decoded_text)
        self.db.save()
        await utils.answer(message, self.strings('notes_restored', message))
