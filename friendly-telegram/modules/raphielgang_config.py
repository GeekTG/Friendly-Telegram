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
    cb(RaphielgangConfig())


class RaphielgangConfig(loader.Module):
    """Stores configuration for Raphielgang modules"""
    def __init__(self):
        self.config = ["API_KEY", "API_HASH", "CONSOLE_LOGGER_VERBOSE", "LOGS", "BOTLOG_CHATID",
                       "BOTLOG", "PM_AUTO_BAN", "DB_URI", "OCR_SPACE_API_KEY", "REM_BG_API_KEY", "CHROME_DRIVER",
                       "GOOGLE_CHROME_BIN", "OPEN_WEATHER_MAP_APPID", "ANTI_SPAMBOT", "ANTI_SPAMBOT_SHOUT",
                       "YOUTUBE_API_KEY", "CLEAN_WELCOME", "BIO_PREFIX", "DEFAULT_BIO", "LASTFM_API",
                       "LASTFM_SECRET", "LASTFM_USERNAME", "LASTFM_PASSWORD_PLAIN", "LASTFM_PASS",
                       "G_DRIVE_CLIENT_ID", "G_DRIVE_CLIENT_SECRET", "G_DRIVE_AUTH_TOKEN_DATA", "GDRIVE_FOLDER_ID",
                       "TEMP_DOWNLOAD_DIRECTORY", "COUNT_MSG", "USERS", "COUNT_PM", "LASTMSG", "ENABLE_KILLME",
                       "CMD_HELP", "BRAIN_CHECKER"]
        self.config = loader.ModuleConfig(*itertools.chain.from_iterable([(x, None, "External configuration item")
                                                                          for x in self.config]))
        self.name = _("Raphielgang Configuration Placeholder")

    def config_complete(self):
        import userbot
        for key, value in self.config.items():
            if value is not None:
                setattr(userbot, key, value)
