from .. import loader, config
import logging
import lyricsgenius

genius = lyricsgenius.Genius(config.GENUIS_API_TOKEN)


def register(cb):
    logging.info('Registering %s', __file__)
    cb(LyricsMod())


class LyricsMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'lyrics': self.lyricscmd}
        self.config = {}
        self.name = "LyricsMod"

    async def lyricscmd(self, message):
        args = message.message.strip(".lyrics").split(",")
        logging.debug("args: " + str(args))
        song = genius.search_song(args[1], args[0])
        await message.edit(song.lyrics)
