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
import itertools

from .. import loader

logger = logging.getLogger(__name__)


def register(cb):
    cb(UniborgConfig())


class UniborgConfig(loader.Module):
    """Stores configuration for Uniborg modules"""
    def __init__(self):
        self.config = ["GOOGLE_CHROME_BIN", "SCREEN_SHOT_LAYER_ACCESS_KEY", "PRIVATE_GROUP_BOT_API_ID",
                       "IBM_WATSON_CRED_USERNAME", "IBM_WATSON_CRED_PASSWORD", "HASH_TO_TORRENT_API",
                       "TELEGRAPH_SHORT_NAME", "OCR_SPACE_API_KEY", "G_BAN_LOGGER_GROUP", "TG_GLOBAL_ALBUM_LIMIT",
                       "TG_BOT_TOKEN_BF_HER", "TG_BOT_USER_NAME_BF_HER", "ANTI_FLOOD_WARN_MODE",
                       "MAX_ANTI_FLOOD_MESSAGES", "CHATS_TO_MONITOR_FOR_ANTI_FLOOD", "REM_BG_API_KEY",
                       "NO_P_M_SPAM", "MAX_FLOOD_IN_P_M_s", "NC_LOG_P_M_S", "PM_LOGGR_BOT_API_ID", "DB_URI",
                       "NO_OF_BUTTONS_DISPLAYED_IN_H_ME_CMD", "COMMAND_HAND_LER", "SUDO_USERS", "VERY_STREAM_LOGIN",
                       "VERY_STREAM_KEY", "G_DRIVE_CLIENT_ID", "G_DRIVE_CLIENT_SECRET", "G_DRIVE_AUTH_TOKEN_DATA",
                       "TELE_GRAM_2FA_CODE", "GROUP_REG_SED_EX_BOT_S", "OPEN_LOAD_LOGIN", "OPEN_LOAD_KEY",
                       "GOOGLE_CHROME_DRIVER"]
        self.config = loader.ModuleConfig(*itertools.chain.from_iterable([(x, None, "External configuration item")
                                                                          for x in self.config]))
        self.name = _("Uniborg Configuration Placeholder")

    def config_complete(self):
        from ..compat import uniborg
        for key, value in self.config.items():
            if value is not None:
                setattr(uniborg.UniborgConfig, key, value)
