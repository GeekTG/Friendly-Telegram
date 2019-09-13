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

from .. import loader, utils

import logging
import lyricsgenius

logger = logging.getLogger(__name__)


def register(cb):
    cb(LyricsMod())


class LyricsMod(loader.Module):
    """Sings songs"""
    def __init__(self):
        self.config = loader.ModuleConfig("GENIUS_API_TOKEN", "",
                                          "The LyricsGenius API token from http://genius.com/api-clients")
        self.name = _("Lyrics")

    def config_complete(self):
        self.genius = lyricsgenius.Genius(self.config["GENIUS_API_TOKEN"])

    async def lyricscmd(self, message):
        """.lyrics Song, Artist"""
        args = utils.get_args_split_by(message, ",")
        if len(args) != 2:
            logger.debug(args)
            await message.edit(_("<code>Please specify song and artist.</code>"))
            return
        logger.debug("getting song lyrics for " + args[0] + ", " + args[1])
        try:
            song = await utils.run_sync(self.genius.search_song, args[0], args[1])
        except TypeError:
            # Song not found causes internal library error
            song = None
        if song is None:
            await message.edit(_("<code>Song not found.</code>"))
            return
        logger.debug(song)
        logger.debug(song.lyrics)
        await utils.answer(message, utils.escape_html(song.lyrics))
