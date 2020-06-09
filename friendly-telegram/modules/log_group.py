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

import telethon
from telethon.tl.types import MessageEntityHashtag, MessageEntityBold, InputPeerSelf
from telethon.tl.types import MessageEntityCode, MessageEntityMentionName, InputPeerUser

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class LoggerMod(loader.Module):
    """Description for module"""
    strings = {"name": "Logger",
               "log_id_cfg": "Chat ID where logs are saved"}

    def __init__(self):
        self.config = loader.ModuleConfig("LOG_ID", None, lambda m: self.strings("log_id_cfg", m))

    async def append_entity(self, id, entities, message):
        fail = True
        try:
            entity = await self._client.get_input_entity(id)
        except ValueError:
            pass
        else:
            if isinstance(entity, InputPeerSelf):
                entity = await self._client.get_me(True)
            if isinstance(entity, InputPeerUser):
                fail = False
                entities.append(MessageEntityMentionName(len(message),
                                len(str(entity.user_id)), entity.user_id))
                message += str(entity.user_id)
        if fail:
            if not isinstance(id, int):
                id = utils.get_entity_id(id)
            entities.append(MessageEntityCode(len(message), len(str(id))))
            message += str(id)
        return message

    async def _log(self, type, group, affected_uids, data):
        """Logs an operation to the group"""
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
            return
        message = "#" + type.upper()
        entities = [MessageEntityHashtag(0, len(message)), MessageEntityBold(0, len(message))]
        if affected_uids:
            message += " "
            for user in affected_uids:
                message = await self.append_entity(user, entities, message)
                message += ", "
            message = message[:-2]
        if group:
            message += " in "
            message = await self.append_entity(group, entities, message)
        if data:
            message += "\n\n" + data
        logger.debug(message)
        await self._client.send_message(chat, message, parse_mode=lambda m: (m, entities))
        if not self._is_bot:
            await self._client(telethon.functions.messages.MarkDialogUnreadRequest(chat, True))

    async def client_ready(self, client, db):
        self._client = client
        self._is_bot = await client.is_bot()
        self.allmodules.register_logger(self._log)
