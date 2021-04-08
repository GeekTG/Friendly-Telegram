#    Friendly Telegram Userbot
#    by GeekTG Team

import logging
import itertools

from .. import loader
from ..compat import uniborg

logger = logging.getLogger(__name__)


@loader.tds
class UniborgConfigMod(loader.Module):
    """Stores configuration for Uniborg modules"""
    strings = {"name": "Uniborg configuration placeholder",
               "cfg_doc": "External configuration item"}

    def __init__(self):
        self.config = filter(lambda x: len(x) and x.upper() == x, uniborg.UniborgConfig.__all__)
        self.config = loader.ModuleConfig(*itertools.chain.from_iterable([(x, None,
                                                                           lambda m: self.strings("cfg_doc", m))
                                                                          for x in self.config]))

    def config_complete(self):
        for key, value in self.config.items():
            if value is not None:
                setattr(uniborg.UniborgConfig, key, value)
