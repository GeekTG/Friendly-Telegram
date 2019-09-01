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
import ast
import asyncio

from . import utils

MODULES_NAME = "modules"


class Module():
    """There is no help for this module"""
    def __init__(self):
        self.name = "Unknown"

    def config_complete(self):
        pass

    # Will always be called after config loaded.
    async def client_ready(self, client, db):
        pass

    async def handle_command(self, message):
        logging.error("NI! handle_command")


class Modules():
    def __init__(self):
        self.commands = {}
        self.modules = []
        self.watchers = []

    def register_all(self, skip, babelfish):
        # from .compat import uniborg  # Uniborg is disabled because it Doesn't Work™️.
        from . import compat  # Avoid circular import
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
                # module.borg = uniborg.UniborgClient()  # Uniborg is disabled because it Doesn't Work™️.
                sys.modules[module_name] = module  # Do this early for the benefit of RaphielGang compat layer
                spec.loader.exec_module(module)
                module._ = babelfish.gettext
                try:
                    module.register(self.register_module, module_name)
                except TypeError:  # Too many arguments
                    module.register(self.register_module)
            except BaseException as e:
                logging.exception("Failed to load module %s due to:", mod)

    def register_module(self, instance):
        if not issubclass(instance.__class__, Module):
            logging.error("Not a subclass %s", repr(instance.__class__))
        if not hasattr(instance, "commands"):
            # https://stackoverflow.com/a/34452/5509575
            instance.commands = {method_name[:-3]: getattr(instance, method_name) for method_name in dir(instance)
                                 if callable(getattr(instance, method_name)) and method_name[-3:] == "cmd"}

        for command in instance.commands:
            # Verify that command does not already exist, or, if it does, the command must be from the same class name
            if command.lower() in self.commands.keys():
                if hasattr(instance.commands[command], "__self__") and \
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
        for com in self.commands:
            logging.debug(com)
            if command.lower() == com:
                logging.debug("found command")
                return self.commands[com](message)  # Returns a coroutine

    def send_config(self, db, additional_config=None):
        for mod in self.modules:
            self.send_config_one(mod, db, additional_config)

    def send_config_one(self, mod, db, additional_config=None):
        if hasattr(mod, "config"):
            modcfg = db.get(mod.__module__, "__config__", {})
            logging.debug(modcfg)
            for conf in mod.config.keys():
                logging.debug(conf)
                if conf in additional_config:
                    mod.config[conf] = ast.literal_eval(additional_config[conf])
                elif conf in modcfg.keys():
                    mod.config[conf] = modcfg[conf]
                else:
                    logging.debug("No config value for " + conf)
            logging.debug(mod.config)
        try:
            mod.config_complete()
        except Exception:
            logging.exception("Failed to send mod config complete signal")

    async def send_ready(self, client, db, allclients):
        self._compat_layer.client_ready(client)
        try:
            for m in self.modules:
                m.allclients = allclients
            await asyncio.gather(*[m.client_ready(client, db) for m in self.modules])
        except Exception:
            logging.exception("Failed to send mod init complete signal")

    def unload_module(self, classname):
        worked = False
        for module in self.modules:
            if module.__class__.__name__ == classname:
                worked = True
                logging.debug("Removing module for unload" + repr(module))
                self.modules.remove(module)
        for watcher in self.watchers:
            if hasattr(watcher, "__self__") and watcher.__self__.__class__.__name__ == classname:
                worked = True
                logging.debug("Removing watcher for unload " + repr(watcher))
                self.watchers.remove(watcher)
        for command in self.commands:
            if hasattr(command, "__self__") and command.__self__.__class__.__name__ == classname:
                worked = True
                logging.debug("Removing command for unload " + repr(command))
                self.commands.remove(command)
        return worked
