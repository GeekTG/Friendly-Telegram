from .. import loader, utils
import logging, lyricsgenius, asyncio, functools



def register(cb):
    logging.info('Registering %s', __file__)
    cb(LyricsMod())


class LyricsMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'lyrics': self.lyricscmd}
        self.config = {"GENUIS_API_TOKEN": ""}
        self.name = "Lyrics"
        self.help = "Sings songs"

    def config_complete(self):
        self.genius = lyricsgenius.Genius(self.config["GENUIS_API_TOKEN"])

    async def lyricscmd(self, message):
        args = utils.get_args_split_by(message, ",")
        logging.debug("getting song lyrics for "+args[0]+", "+args[1])
        song = await asyncio.get_event_loop().run_in_executor(None, functools.partial(self.genius.search_song, args[0], args[1]))
        logging.debug(song)
        logging.debug(song.lyrics)
        #song = self.genius.search_song(args[1], args[0])
        await message.edit(utils.escape_html(song.lyrics))
