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

import userbot  # see .compat
from .. import loader

logger = logging.getLogger(__name__)


def register(cb):
    cb(RaphielgangConfig())


class RaphielgangConfig(loader.Module):
    """Stores configuration for Raphielgang modules"""
    def __init__(self):
        self.config = filter(lambda x: len(x) and x.upper() == x, userbot.__all__)
        self.config = loader.ModuleConfig(*itertools.chain.from_iterable([(x, None, "External configuration item")
                                                                          for x in self.config]))
        self.name = _("Raphielgang Configuration Placeholder")

    def config_complete(self):
        for key, value in self.config.items():
            if value is not None:
                setattr(userbot, key, value)
