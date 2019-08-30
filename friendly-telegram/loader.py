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
        from . import compat  # Avoid circular import
        self._compat_layer = compat.activate([])
        logging.debug(os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), MODULES_NAME)))
        mods = filter(lambda x: (len(x) > 3 and x[-3:] == ".py" and x[0] != "_"),
                      os.listdir(os.path.join(utils.get_base_dir(), MODULES_NAME)))
        logging.debug(mods)
        for mod in mods:
            mod = mod[:-3]  # Cut .py
            try:
                importlib.import_module("." + MODULES_NAME + "." + mod, __package__)
                mod = __package__ + "." + MODULES_NAME + "." + mod  # FQN
                if mod in skip:
                    logging.debug("Not loading module %s because it is blacklisted", mod)
                    continue
                sys.modules[mod]._ = babelfish.gettext
                try:
                    sys.modules[mod].register(self.register_module, mod)
                except TypeError:  # Too many arguments
                    sys.modules[mod].register(self.register_module)
            except BaseException as e:
                logging.exception("Failed to load module %s due to:", mod)
            finally:
                try:
                    del sys.modules[mod]
                except BaseException as e:
                    logging.exception("Failed to clear namespace of module %s due to:", mod)

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
