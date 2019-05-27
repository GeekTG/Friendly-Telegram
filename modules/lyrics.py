from .. import loader, config
import logging
import lyricsgenius



def register(cb):
    logging.info('Registering %s', __file__)
    cb(LyricsMod())


class LyricsMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'lyrics': self.lyricscmd}
        self.config = {"GENUIS_API_TOKEN": ""}
        self.name = "LyricsMod"

    def config_complete(self):
        self.genius = lyricsgenius.Genius(self.config["GENUIS_API_TOKEN"])

    async def lyricscmd(self, message):
        args = utils.get_args(message)
        logging.debug("getting song lyrics for "+args[0]+": "+args[1])
        song = self.genius.search_song(args[1], args[0])
        await message.edit(song.lyrics)
