"""
    █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
    █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█

    Copyright 2022 t.me/hikariatama
    Licensed under the Creative Commons CC BY-NC-ND 4.0

    Full license text can be found at:
    https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode

    Human-friendly one:
    https://creativecommons.org/licenses/by-nc-nd/4.0
"""

# <3 title: Backuper
# <3 pic: https://img.icons8.com/fluency/48/000000/sync-settings.png
# <3 desc: Create the backup of all modules, notes, the whole database

from .. import loader, utils
import asyncio
import datetime
import io
import json

from telethon.tl.types import Message


@loader.tds
class BackuperMod(loader.Module):
    """Backup everything and anything"""
    strings = {
        "name": "Backuper",
        'backup_caption': '☝️ <b>Это - бекап базы данных. Никому его не передавай</b>',
        'reply_to_file': '<b>Reply to .{} file</b>',
        'db_restored': '<b>База данных обновлена. Перезапускаю юзербот...</b>',
        'modules_backup': '🦊 <b>Резервная копия модулей ({})</b>',
        'notes_backup': '🦊 <b>Резервная копия заметок ({})</b>',
        'mods_restored': '🦊 <b>Моды восстановлены, перезагружаюсь</b>',
        'notes_restored': '🦊 <b>Заметки восстановлены</b>'
    }

    async def client_ready(self, client, db):
        self.db = db
        self.client = client

    async def backupdbcmd(self, message: Message) -> None:
        """Create database backup [will be sent in pm]"""
        txt = io.BytesIO(json.dumps(self.db).encode('utf-8'))
        txt.name = f"ftg-db-backup-{datetime.now().strftime('%d-%m-%Y-%H-%M')}.db"
        await self.client.send_file('me', txt, caption=self.strings('backup_caption'))
        await message.delete()

    async def restoredbcmd(self, message: Message) -> None:
        """Restore database from file"""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            await utils.answer(message, self.strings('reply_to_file', message).format('db'))
            await asyncio.sleep(3)
            await message.delete()
            return

        file = await message.client.download_file(reply.media)
        decoded_text = json.loads(file.decode('utf-8'))
        self.db.clear()
        self.db.update(**decoded_text)
        self.db.save()
        # print(decoded_text)
        await utils.answer(message, self.strings('db_restored', message))
        await self.allmodules.commands['restart'](await message.respond('_'))

    async def backupmodscmd(self, message: Message) -> None:
        """Create backup of mods"""
        data = json.dumps({'loaded': self.db.get("friendly-telegram.modules.loader", "loaded_modules", []),
                           'unloaded': []})
        txt = io.BytesIO(data.encode('utf-8'))
        txt.name = f"ftg-mods-{datetime.now().strftime('%d-%m-%Y-%H-%M')}.mods"
        await self.client.send_file(utils.get_chat_id(message), txt, caption=self.strings('modules_backup', message).format(len(self.db.get("friendly-telegram.modules.loader", "loaded_modules", []))))
        await message.delete()

    async def restoremodscmd(self, message: Message) -> None:
        """<reply to file> - Restore mods from backup"""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            await utils.answer(message, self.strings('reply_to_file', message).format('mods'))
            await asyncio.sleep(3)
            await message.delete()
            return

        file = await message.client.download_file(reply.media)
        decoded_text = json.loads(file.decode('utf-8'))
        self.db.set("friendly-telegram.modules.loader",
                    "loaded_modules", decoded_text['loaded'])
        self.db.set("friendly-telegram.modules.loader",
                    "unloaded_modules", decoded_text['unloaded'])
        self.db.save()
        await utils.answer(message, self.strings('mods_restored', message))
        await self.allmodules.commands['restart'](await message.respond('_'))

    async def backupnotescmd(self, message: Message) -> None:
        """Create the backup of notes"""
        data = json.dumps(self.db.get(
            "friendly-telegram.modules.notes", "notes", []))
        txt = io.BytesIO(data.encode('utf-8'))
        txt.name = f"ftg-notes-{datetime.now().strftime('%d-%m-%Y-%H-%M')}.notes"
        await self.client.send_file(utils.get_chat_id(message), txt, caption=self.strings('notes_backup', message).format(len(self.db.get("friendly-telegram.modules.notes", "notes", []))))
        await message.delete()

    async def restorenotescmd(self, message: Message) -> None:
        """<reply to file> - Restore notes from backup"""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            await utils.answer(message, self.strings('reply_to_file', message).format('notes'))
            await asyncio.sleep(3)
            await message.delete()
            return

        file = await message.client.download_file(reply.media)
        decoded_text = json.loads(file.decode('utf-8'))
        self.db.set("friendly-telegram.modules.notes", "notes", decoded_text)
        self.db.save()
        await utils.answer(message, self.strings('notes_restored', message))
