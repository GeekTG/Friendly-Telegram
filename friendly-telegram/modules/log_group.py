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

import logging

from telethon.tl.types import MessageEntityHashtag, MessageEntityBold, MessageEntityCode, MessageEntityMentionName

from .. import loader

logger = logging.getLogger(__name__)


def register(cb):
    cb(LoggerMod())


class LoggerMod(loader.Module):
    """Description for module"""
    def __init__(self):
        self.config = loader.ModuleConfig("LOG_ID", None, _("Chat ID where logs are saved"))
        self.name = _("Logger")

    async def _log(self, type, group, affected_uids, data):
        """Logs an operation to the group"""
        message = "#"
        message += type
        entities = [MessageEntityHashtag(0, len(message)), MessageEntityBold(0, len(message))]
        if affected_uids:
            message += " in "
            for user in affected_uids:
                try:
                    await self._client.get_input_entity(user)
                except ValueError:
                    entities.append(MessageEntityCode(len(message), len(str(user))))
                else:
                    entities.append(MessageEntityMentionName(len(message), len(str(user)), user))
                message += str(user) + ", "
            message = message[:-2]
        if group:
            message += " in "
            entities.append(MessageEntityCode(len(message), len(str(group))))
            message += str(group)
        if data:
            message += "\n\n" + data
        logger.debug(message)
        chat = None
        if self.config["LOG_ID"]:
            try:
                chat = await self._client.get_entity(self.config["LOG_ID"])
            except ValueError:
                logger.debug("ent not found", exc_info=True)
                async for dialog in self._client.iter_dialogs():
                    if dialog.id == self.config["LOG_ID"] or abs(dialog.id + 1000000000000) == self.config["LOG_ID"]:
                        chat = dialog.entity
                        break
            if chat is None:
                logger.debug("chat not found")
            else:
                await self._client.send_message(chat, message, parse_mode=lambda m: (m, entities))

    async def client_ready(self, client, db):
        self._client = client
        self.allmodules.register_logger(self._log)
