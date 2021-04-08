#    Friendly Telegram Userbot
#    by GeekTG Team

import logging
import itertools

import userbot  # see .compat
from .. import loader

logger = logging.getLogger(__name__)


@loader.tds
class RaphielgangConfigMod(loader.Module):
    """Stores configuration for Raphielgang modules"""
    strings = {"name": "Raphielgang Configuration Placeholder",
               "cfg_doc": "External configuration item"}

    def __init__(self):
        self.config = filter(lambda x: len(x) and x.upper() == x, userbot.__all__)
        self.config = loader.ModuleConfig(*itertools.chain.from_iterable([(x, None,
                                                                           lambda m: self.strings("cfg_doc", m))
                                                                          for x in self.config]))

    def config_complete(self):
        for key, value in self.config.items():
            if value is not None:
                setattr(userbot, key, value)
