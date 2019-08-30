import sys
import logging

from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec

from .raphielgang import RaphielgangConfig, RaphielgangEvents


# When a name is matched, the import is overriden, and our custom object is returned
modules = {"userbot": RaphielgangConfig, "userbot.events": RaphielgangEvents}


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

    def client_ready(self, client):
        for mod in self.created:
            try:
                mod.client_ready(client)
            except BaseException:
                logging.exception("Failed to send client_ready to compat layer " + repr(mod))


def activate(clients):
    compatlayer = BotCompat(clients)
    sys.meta_path.insert(0, compatlayer)
    return compatlayer
