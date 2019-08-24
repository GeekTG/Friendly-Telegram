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
                sys.modules[mod].register(self.register_module)
            except BaseException as e:
                logging.exception("Failed to load module %s due to:", mod)
            finally:
                try:
                    del sys.modules[mod]
                except BaseException as e:
                    logging.exception("Failed to clear namespace of module %s due to:", mod)
                    pass

    def register_module(self, instance):
        if not issubclass(instance.__class__, Module):
            logging.error("Not a subclass %s", repr(instance.__class__))
        if not hasattr(instance, "commands"):
            # https://stackoverflow.com/a/34452/5509575
            instance.commands = {method_name[:-3]: getattr(instance, method_name) for method_name in dir(instance)
                                 if callable(getattr(instance, method_name)) and method_name[-3:] == "cmd"}

        for command in instance.commands:
            if command.lower() in self.commands.keys():
                logging.error("Duplicate command %s", command)
                continue
            if not instance.commands[command].__doc__:
                logging.warning("Missing docs for %s", command)
            self.commands.update({command.lower(): instance.commands[command]})
        try:
            if instance.watcher:
                self.watchers += [instance.watcher]
        except AttributeError:
            pass
        if hasattr(instance, "allmodules"):
            # Mainly for the Help module
            instance.allmodules = self
        self.modules += [instance]

    def dispatch(self, command, message):
        logging.debug(self.commands)
        for com in self.commands:
            logging.debug(com)
            if command.lower() == "." + com:
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
        try:
            for m in self.modules:
                m.allclients = allclients
            await asyncio.gather(*[m.client_ready(client, db) for m in self.modules])
        except Exception:
            logging.exception("Failed to send mod init complete signal")
