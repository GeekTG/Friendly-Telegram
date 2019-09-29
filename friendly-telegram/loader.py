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

import importlib
import importlib.util
import os
import logging
import sys
import asyncio
import inspect

from . import utils

MODULES_NAME = "modules"


class ModuleConfig(dict):
    def __init__(self, *entries):
        i = 0
        keys = []
        values = []
        docstrings = []
        for entry in entries:
            if i % 3 == 0:
                keys.append(entry)
            elif i % 3 == 1:
                values.append(entry)
            else:
                docstrings.append(entry)
            i += 1
        super().__init__(zip(keys, values))
        self.docstrings = dict(zip(keys, docstrings))

    def getdoc(self, key):
        return self.docstrings[key]


class Module():
    """There is no help for this module"""
    def __init__(self):
        self.name = "Unknown"

    def config_complete(self):
        pass

    # Will always be called after config loaded.
    async def client_ready(self, client, db):
        pass

    # Called after client_ready, for internal use only. Must not be used by non-core modules
    async def _client_ready2(self, client, db):
        pass


class Modules():
    def __init__(self):
        self.commands = {}
        self.aliases = {}
        self.modules = []
        self.watchers = []

    def register_all(self, skip, babelfish):
        from .compat import uniborg
        from . import compat  # Avoid circular import
        self._skip = skip
        self._compat_layer = compat.activate([])
        logging.debug(os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), MODULES_NAME)))
        mods = filter(lambda x: (len(x) > 3 and x[-3:] == ".py" and x[0] != "_"),
                      os.listdir(os.path.join(utils.get_base_dir(), MODULES_NAME)))
        logging.debug(mods)
        for mod in mods:
            try:
                module_name = __package__ + "." + MODULES_NAME + "." + mod[:-3]  # FQN
                if module_name in skip:
                    logging.debug("Not loading module %s because it is blacklisted", module_name)
                    continue
                logging.debug(module_name)
                logging.debug(os.path.join(utils.get_base_dir(), MODULES_NAME, mod))
                spec = importlib.util.spec_from_file_location(module_name,
                                                              os.path.join(utils.get_base_dir(), MODULES_NAME, mod))
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module  # Do this early for the benefit of RaphielGang compat layer
                module.borg = uniborg.UniborgClient(module_name)
                spec.loader.exec_module(module)
                module._ = babelfish.gettext
                try:
                    module.register(self.register_module, module_name)
                except TypeError:  # Too many arguments
                    module.register(self.register_module)
            except BaseException as e:
                logging.exception("Failed to load module %s due to:", mod)

    def register_module(self, instance):
        if not issubclass(type(instance), Module):
            logging.error("Not a subclass %s", repr(instance.__class__))
        if not hasattr(instance, "commands"):
            # https://stackoverflow.com/a/34452/5509575
            instance.commands = {method_name[:-3]: getattr(instance, method_name) for method_name in dir(instance)
                                 if callable(getattr(instance, method_name)) and method_name[-3:] == "cmd"}

        if inspect.getmodule(type(instance)).__name__ in self._skip:
            logging.debug("Not loading module %s because it is blacklisted", type(instance).__name__)
            return
        for command in instance.commands:
            # Verify that command does not already exist, or, if it does, the command must be from the same class name
            if command.lower() in self.commands.keys():
                if hasattr(instance.commands[command], "__self__") and \
                        hasattr(self.commands[command], "__self__") and \
                        instance.commands[command].__self__.__class__.__name__ \
                        != self.commands[command].__self__.__class__.__name__:
                    logging.error("Duplicate command %s", command)
                    continue
                else:
                    logging.debug("Replacing command for update " + repr(self.commands[command]))
            if not instance.commands[command].__doc__:
                logging.warning("Missing docs for %s", command)
            self.commands.update({command.lower(): instance.commands[command]})
        try:
            if instance.watcher:
                for watcher in self.watchers:
                    if hasattr(watcher, "__self__") and watcher.__self__.__class__.__name__ \
                            == instance.watcher.__self__.__class__.__name__:
                        logging.debug("Removing watcher for update " + repr(watcher))
                        self.watchers.remove(watcher)
                self.watchers += [instance.watcher]
        except AttributeError:
            pass
        if hasattr(instance, "allmodules"):
            # Mainly for the Help module
            instance.allmodules = self
        for module in self.modules:
            if module.__class__.__name__ == instance.__class__.__name__:
                logging.debug("Removing module for update " + repr(module))
                self.modules.remove(module)
        self.modules += [instance]

    def dispatch(self, command, message):
        logging.debug(self.commands)
        logging.debug(self.aliases)
        for com in self.commands:
            if command.lower() == com:
                logging.debug("found command")
                return self.commands[com](message)  # Returns a coroutine
        for alias in self.aliases.keys():
            if alias.lower() == command.lower():
                logging.debug("found alias")
                com = self.aliases[alias]
                try:
                    message.message = com + message.message[len(command):]
                    return self.commands[com](message)
                except KeyError:
                    logging.warning("invalid alias")

    def send_config(self, db):
        for mod in self.modules:
            self.send_config_one(mod, db)

    def send_config_one(self, mod, db):
        if hasattr(mod, "config"):
            modcfg = db.get(mod.__module__, "__config__", {})
            logging.debug(modcfg)
            for conf in mod.config.keys():
                logging.debug(conf)
                if conf in modcfg.keys():
                    mod.config[conf] = modcfg[conf]
                else:
                    logging.debug("No config value for " + conf)
            logging.debug(mod.config)
        try:
            mod.config_complete()
        except Exception:
            logging.exception("Failed to send mod config complete signal")

    async def send_ready(self, client, db, allclients):
        await self._compat_layer.client_ready(client)
        try:
            for m in self.modules:
                m.allclients = allclients
            await asyncio.gather(*[m.client_ready(client, db) for m in self.modules])
            await asyncio.gather(*[m._client_ready2(client, db) for m in self.modules])
        except Exception:
            logging.exception("Failed to send mod init complete signal")

    def unload_module(self, classname):
        worked = []
        to_remove = []
        for module in self.modules:
            if module.__class__.__name__ == classname or module.name == classname:
                worked += [module.__module__]
                logging.debug("Removing module for unload" + repr(module))
                self.modules.remove(module)
                to_remove += module.commands.values()
                if hasattr(module, "watcher"):
                    to_remove += [module.watcher]
        logging.debug("to_remove: %r", to_remove)
        for watcher in self.watchers.copy():
            if watcher in to_remove:
                logging.debug("Removing watcher for unload " + repr(watcher))
                self.watchers.remove(watcher)
        aliases_to_remove = []
        for name, command in self.commands.copy().items():
            if command in to_remove:
                logging.debug("Removing command for unload " + repr(command))
                del self.commands[name]
                aliases_to_remove.append(name)
        for alias, command in self.aliases.copy().items():
            if command in aliases_to_remove:
                del self.aliases[alias]
        return worked

    def add_alias(self, alias, cmd):
        if cmd not in self.commands.keys():
            return False
        self.aliases[alias] = cmd
        return True

    def remove_alias(self, alias):
        try:
            del self.aliases[alias]
        except KeyError:
            return False
        return True
