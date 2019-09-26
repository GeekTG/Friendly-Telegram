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

import sys
import logging

from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec

from .raphielgang import RaphielgangConfig, RaphielgangEvents
from .uniborg import UniborgUtil, Uniborg


# When a name is matched, the import is overriden, and our custom object is returned
modules = {"userbot": RaphielgangConfig, "userbot.events": RaphielgangEvents,
           "uniborg": Uniborg, "uniborg.util": UniborgUtil}


class BotCompat(MetaPathFinder, Loader):
    def __init__(self, clients):
        self.clients = clients
        self.created = []

    def find_spec(self, fullname, path, target=None):
        if fullname in modules:
            return ModuleSpec(fullname, self)

    def create_module(self, spec):
        ret = modules[spec.name](self.clients)
        self.created += [ret]
        return ret

    def exec_module(self, module):
        module.__path__ = []

    async def client_ready(self, client):
        self.clients += [client]
        for mod in self.created:
            try:
                await mod.client_ready(client)
            except BaseException:
                logging.exception("Failed to send client_ready to compat layer " + repr(mod))


def activate(clients):
    compatlayer = BotCompat(clients)
    sys.meta_path.insert(0, compatlayer)
    return compatlayer
