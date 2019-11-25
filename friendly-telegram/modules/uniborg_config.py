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
from ..compat import uniborg

logger = logging.getLogger(__name__)


def register(cb):
    cb(UniborgConfig())


class UniborgConfig(loader.Module):
    """Stores configuration for Uniborg modules"""
    strings = {"name": "Uniborg configuration placeholder",
               "cfg_doc": "External configuration item"}

    def __init__(self):
        self.config = filter(lambda x: len(x) and x.upper() == x, uniborg.UniborgConfig.__all__)
        self.config = loader.ModuleConfig(*itertools.chain.from_iterable([(x, None, lambda: self.strings["cfg_doc"])
                                                                          for x in self.config]))

    def config_complete(self):
        self.name = self.strings["name"]
        for key, value in self.config.items():
            if value is not None:
                setattr(uniborg.UniborgConfig, key, value)
