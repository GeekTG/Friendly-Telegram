from .util import get_cmd_name, MarkdownBotPassthrough
from .. import loader

from functools import wraps

import logging
import telethon
import sys
import re
import datetime
import tempfile

logger = logging.getLogger(__name__)


class UniborgClient:
    class __UniborgShimMod__Base(loader.Module):
        def __init__(self, borg):
            self._borg = borg
            self.commands = borg._commands
            self.name = type(self).__name__

        async def watcher(self, message):
            for w in self._borg._watchers:
                w(message)

        async def client_ready(self, client, db):
            self._client = client

    def registerfunc(self, cb):
        self._wrapper = type("UniborgShim__" + self._module, (self.__UniborgShimMod__Base,), dict())(self)
        cb(self._wrapper)

    def __init__(self):
        self._storage = None  # TODO
        self._config = UniborgConfig()
        self._commands = {}
        self._watchers = []
        self._wrapper = None  # Set in registerfunc

    def on(self, event):
        def subreg(func):
            logger.debug(event)

            self._module = func.__module__
            sys.modules[self._module].__dict__["register"] = self.registerfunc
            sys.modules[self._module].__dict__["logger"] = logging.getLogger(self._module)
            sys.modules[self._module].__dict__["storage"] = self._storage
            sys.modules[self._module].__dict__["Config"] = self._config

            if event.outgoing:
                # Command based thing
                if not event.pattern:
                    logger.error("Unable to register for outgoing messages without pattern.")
                    return func
                cmd = get_cmd_name(event.pattern.__self__.pattern)
                if not cmd:
                    return func

                @wraps(func)
                def commandhandler(message):
                    """Closure to execute command when handler activated and regex matched"""
                    logger.debug("Command triggered")
                    match = re.match(event.pattern.__self__.pattern, "." + message.message, re.I)
                    if match:
                        logger.debug("and matched")
                        message.message = "." + message.message  # Framework strips prefix, give them a generic one
                        event2 = MarkdownBotPassthrough(message)
                        # Try to emulate the expected format for an event
                        event2.text = list(str(message.message))
                        event2.pattern_match = match
                        event2.message = MarkdownBotPassthrough(message)

                        # Put it off as long as possible so event handlers register
                        sys.modules[self._module].__dict__["borg"] = self._wrapper._client

                        return func(event2)
                        # Return a coroutine
                    else:
                        logger.debug("but not matched cmd " + message.message
                                     + " regex " + event.pattern.__self__.pattern)
                self._commands[cmd] = commandhandler
            elif event.incoming:
                @wraps(func)
                def watcherhandler(message):
                    """Closure to execute watcher when handler activated and regex matched"""
                    match = re.match(event.pattern.__self__.pattern, message.message, re.I)
                    if match:
                        logger.debug("and matched")
                        message.message = message.message  # Framework strips prefix, give them a generic one
                        event2 = MarkdownBotPassthrough(message)
                        # Try to emulate the expected format for an event
                        event2.text = list(str(message.message))
                        event2.pattern_match = match
                        event2.message = MarkdownBotPassthrough(message)

                        return func(event2)
                        # Return a coroutine
                self._watchers += [watcherhandler]  # Add to list of watchers so we can call later.
            else:
                logger.error("event not incoming or outgoing")
                return func
            return func
        return subreg


class Uniborg:
    def __init__(self, clients):
        self.__all__ = "util"


class UniborgUtil:
    def __init__(self, clients):
        pass

    def admin_cmd(self, *args, **kwargs):
        """Uniborg uses this for sudo users but we don't have that concept."""
        if len(args) > 0:
            if len(args) != 1:
                raise TypeError("Takes exactly 0 or 1 args")
            kwargs["pattern"] = args[0]
        if not (kwargs["pattern"].startswith(".") or kwargs["pattern"].startswith(r"\.")):
            kwargs["pattern"] = r"\." + kwargs["pattern"]
        if not ("incoming" in kwargs.keys() or "outgoing" in kwargs.keys()):
            kwargs["outgoing"] = True
        return telethon.events.NewMessage(**kwargs)

    async def progress(self, *args, **kwargs):
        pass

    async def is_read(self, *args, **kwargs):
        return False  # Meh.

    def humanbytes(self, size):
        return str(size) + " bytes"  # Meh.

    def time_formatter(ms):
        return str(datetime.timedelta(milliseconds=ms))


class UniborgConfig:
    TMP_DOWNLOAD_DIRECTORY = tempfile.mkdtemp()

    def __init__(self):
        self.GOOGLE_CHROME_BIN = None
        self.SCREEN_SHOT_LAYER_ACCESS_KEY = None
        self.PRIVATE_GROUP_BOT_API_ID = None
        # self.TMP_DOWNLOAD_DIRECTORY = tempfile.mkdtmp()  # static
        self.IBM_WATSON_CRED_USERNAME = None
        self.IBM_WATSON_CRED_PASSWORD = None
        self.HASH_TO_TORRENT_API = None
        self.TELEGRAPH_SHORT_NAME = "UniborgShimFriendlyTelegram"
        self.OCR_SPACE_API_KEY = None
        self.G_BAN_LOGGER_GROUP = None
        self.TG_GLOBAL_ALBUM_LIMIT = 9  # What does this do o.O?
        self.TG_BOT_TOKEN_BF_HER = None
        self.TG_BOT_USER_NAME_BF_HER = None
        self.ANTI_FLOOD_WARN_MODE = None
        self.MAX_ANTI_FLOOD_MESSAGES = 10
        self.CHATS_TO_MONITOR_FOR_ANTI_FLOOD = []
        self.REM_BG_API_KEY = None
        self.NO_P_M_SPAM = False
        self.MAX_FLOOD_IN_P_M_s = 3  # Default from spechide
        self.NC_LOG_P_M_S = False
        self.PM_LOGGR_BOT_API_ID = -100
        self.DB_URI = None
        self.NO_OF_BUTTONS_DISPLAYED_IN_H_ME_CMD = 5
        self.COMMAND_HAND_LER = r"\."
        self.SUDO_USERS = set()  # Don't add anyone here!
        self.VERY_STREAM_LOGIN = None
        self.VERY_STREAM_KEY = None
        self.G_DRIVE_CLIENT_ID = None
        self.G_DRIVE_CLIENT_SECRET = None
        self.G_DRIVE_AUTH_TOKEN_DATA = None
        self.TELE_GRAM_2FA_CODE = None
        self.GROUP_REG_SED_EX_BOT_S = None
        self.OPEN_LOAD_LOGIN = None
        self.OPEN_LOAD_KEY = None
        self.GOOGLE_CHROME_DRIVER = None
        self.GOOGLE_CHROME_BIN = None

        # === SNIP ===
        # this stuff should never get changed, because its either unused or dangerous
        self.MAX_MESSAGE_SIZE_LIMIT = 4095
        self.UB_BLACK_LIST_CHAT = set()
        self.LOAD = []
        self.NO_LOAD = []
        self.CHROME_DRIVER = self.GOOGLE_CHROME_DRIVER
        self.CHROME_BIN = self.GOOGLE_CHROME_BIN
