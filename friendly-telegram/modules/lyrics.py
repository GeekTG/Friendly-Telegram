from .. import loader, utils
import logging, lyricsgenius

logger = logging.getLogger(__name__)

def register(cb):
    cb(LyricsMod())


class LyricsMod(loader.Module):
    """Sings songs"""
    def __init__(self):
        self.commands = {'lyrics': self.lyricscmd}
        self.config = {"GENIUS_API_TOKEN": ""}
        self.name = "Lyrics"

    def config_complete(self):
        self.genius = lyricsgenius.Genius(self.config["GENIUS_API_TOKEN"])

    async def lyricscmd(self, message):
        """.lyrics Song, Artist"""
        args = utils.get_args_split_by(message, ",")
        logger.debug("getting song lyrics for "+args[0]+", "+args[1])
        song = await utils.run_sync(self.genius.search_song, args[0], args[1])
        logger.debug(song)
        logger.debug(song.lyrics)
        #song = self.genius.search_song(args[1], args[0])
        await message.edit(utils.escape_html(song.lyrics))
