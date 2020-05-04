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

"""Loads modules from disk and dispatches stuff, and stores state"""

import importlib
import importlib.util
import os
import logging
import sys
import asyncio
import functools
import inspect

from . import utils

MODULES_NAME = "modules"


def translatable_docstring(cls):
    @functools.wraps(cls.config_complete)
    def config_complete(self, *args, **kwargs):
        for command, func in get_commands(cls).items():
            try:
                func.__doc__ = self.strings["_cmd_doc_" + command]
            except AttributeError:
                func.__func__.__doc__ = self.strings["_cmd_doc_" + command]
        self.__doc__ = self.strings["_cls_doc"]
        return self.config_complete._old_(self, *args, **kwargs)
    config_complete._old_ = cls.config_complete
    cls.config_complete = config_complete
    for command, func in get_commands(cls).items():
        cls.strings["_cmd_doc_" + command] = inspect.getdoc(func)
    cls.strings["_cls_doc"] = inspect.getdoc(cls)
    return cls


tds = translatable_docstring  # Shorter name for modules to use


class ModuleConfig(dict):
    """Like a dict but contains doc for each key"""
    def __init__(self, *entries):
        i = 0
        keys = []
        values = []
        defaults = []
        docstrings = []
        for entry in entries:
            if i % 3 == 0:
                keys.append(entry)
            elif i % 3 == 1:
                values.append(entry)
                defaults.append(entry)
            else:
                docstrings.append(entry)
            i += 1
        super().__init__(zip(keys, values))
        self._docstrings = dict(zip(keys, docstrings))
        self._defaults = dict(zip(keys, defaults))

    def getdoc(self, key):
        """Get the documentation by key"""
        ret = self._docstrings[key]
        if callable(ret):
            ret = ret()
            self._docstrings[key] = ret
        return ret

    def getdef(self, key):
        """Get the default value by key"""
        return self._defaults[key]


class Module():
    """There is no help for this module"""
    def __init__(self):
        self.name = "Unknown"

    def config_complete(self):
        """Will be called when module.config is populated"""

    async def client_ready(self, client, db):
        """Will be called after client is ready (after config_loaded)"""

    # Called after client_ready, for internal use only. Must not be used by non-core modules
    async def _client_ready2(self, client, db):
        pass


def get_commands(mod):
    # https://stackoverflow.com/a/34452/5509575
    return {method_name[:-3]: getattr(mod, method_name) for method_name in dir(mod)
            if callable(getattr(mod, method_name)) and method_name[-3:] == "cmd"}


class Modules():
    """Stores all registered modules"""
    instances = []

    def __init__(self):
        self.commands = {}
        self.aliases = {}
        self.modules = []
        self.watchers = []
        self._compat_layer = None
        self._log_handlers = []
        self.instances.append(self)
        self.client = None

    def register_all(self, babelfish, mods=None):
        """Load all modules in the module directory"""
        if self._compat_layer is None:
            from .compat import uniborg
            from . import compat  # Avoid circular import
            self._compat_layer = compat.activate([])
        logging.debug(os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), MODULES_NAME)))
        if not mods:
            mods = filter(lambda x: (len(x) > 3 and x[-3:] == ".py" and x[0] != "_"),
                          os.listdir(os.path.join(utils.get_base_dir(), MODULES_NAME)))
        logging.debug(mods)
        for mod in mods:
            try:
                module_name = __package__ + "." + MODULES_NAME + "." + mod[:-3]  # FQN
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
            except BaseException:
                logging.exception("Failed to load module %s due to:", mod)

    def register_module(self, instance):
        """Register single module instance"""
        if not issubclass(type(instance), Module):
            logging.error("Not a subclass %s", repr(instance.__class__))
        self.complete_registration(instance)

    def register_commands(self, instance):
        """Register commands from instance"""
        for command in instance.commands:
            # Verify that command does not already exist, or, if it does, the command must be from the same class name
            if command.lower() in self.commands.keys():
                if hasattr(instance.commands[command], "__self__") and \
                        hasattr(self.commands[command], "__self__") and \
                        instance.commands[command].__self__.__class__.__name__ \
                        != self.commands[command].__self__.__class__.__name__:
                    logging.error("Duplicate command %s", command)
                logging.debug("Replacing command for %r", self.commands[command])
            if not instance.commands[command].__doc__:
                logging.warning("Missing docs for %s", command)
            self.commands.update({command.lower(): instance.commands[command]})

    def register_watcher(self, instance):
        """Register watcher from instance"""
        try:
            if instance.watcher:
                for watcher in self.watchers:
                    if hasattr(watcher, "__self__") and watcher.__self__.__class__.__name__ \
                            == instance.watcher.__self__.__class__.__name__:
                        logging.debug("Removing watcher for update %r", watcher)
                        self.watchers.remove(watcher)
                self.watchers += [instance.watcher]
        except AttributeError:
            pass

    def complete_registration(self, instance):
        """Complete registration of instance"""
        # Mainly for the Help module
        instance.allmodules = self
        # And for Remote
        instance.allloaders = self.instances
        instance.log = self.log  # Like botlog from PP
        for module in self.modules:
            if module.__class__.__name__ == instance.__class__.__name__:
                logging.debug("Removing module for update %r", module)
                self.modules.remove(module)
        self.modules += [instance]

    def dispatch(self, command):
        """Dispatch command to appropriate module"""
        try:
            return command, self.commands[command.lower()]
        except KeyError:
            try:
                cmd = self.aliases[command.lower()]
                return cmd, self.commands[cmd.lower()]
            except KeyError:
                return command, None

    def send_config(self, db, babel, skip_hook=False):
        """Configure modules"""
        for mod in self.modules:
            self.send_config_one(mod, db, babel, skip_hook)

    def send_config_one(self, mod, db, babel=None, skip_hook=False):  # pylint: disable=R0201
        """Send config to single instance"""
        if hasattr(mod, "config"):
            modcfg = db.get(mod.__module__, "__config__", {})
            logging.debug(modcfg)
            for conf in mod.config.keys():
                logging.debug(conf)
                if conf in modcfg.keys():
                    mod.config[conf] = modcfg[conf]
                else:
                    try:
                        mod.config[conf] = os.environ[mod.__module__ + "." + conf]
                        logging.debug("Loaded config key %s from environment", conf)
                    except KeyError:
                        logging.debug("No config value for %s", conf)
                        mod.config[conf] = mod.config.getdef(conf)
            logging.debug(mod.config)
        if hasattr(mod, "strings") and babel is not None:
            mod.strings = mod.strings.copy()  # For users with many accounts with diff. translations
            for key, value in mod.strings.items():
                new = babel.getkey(mod.__module__ + "." + key)
                if new is not False:
                    mod.strings[key] = new
        if skip_hook:
            return
        mod.babel = babel
        try:
            mod.config_complete()
        except Exception:
            logging.exception("Failed to send mod config complete signal")

    async def send_ready(self, client, db, allclients):
        """Send all data to all modules"""
        self.client = client
        await self._compat_layer.client_ready(client)
        try:
            await asyncio.gather(*[self.send_ready_one(mod, client, db, allclients, True) for mod in self.modules])
            await asyncio.gather(*[mod._client_ready2(client, db) for mod in self.modules])  # pylint: disable=W0212
        except Exception:
            logging.exception("Failed to send mod init complete signal")

    async def send_ready_one(self, mod, client, db, allclients, core=False):
        mod.allclients = allclients
        try:
            await mod.client_ready(client, db)
        except Exception:
            logging.exception("Failed to send mod init complete signal for %r", mod)
        if not hasattr(mod, "commands"):
            mod.commands = get_commands(mod)

        self.register_commands(mod)
        self.register_watcher(mod)

    def get_classname(self, name):
        for module in reversed(self.modules):
            if name in (module.name, module.__class__.__module__):
                return module.__class__.__module__
        return name

    def unload_module(self, classname):
        """Remove module and all stuff from it"""
        worked = []
        to_remove = []
        for module in self.modules:
            if classname in (module.name, module.__class__.__name__):
                worked += [module.__module__]
                logging.debug("Removing module for unload %r", module)
                self.modules.remove(module)
                to_remove += module.commands.values()
                if hasattr(module, "watcher"):
                    to_remove += [module.watcher]
        logging.debug("to_remove: %r", to_remove)
        for watcher in self.watchers.copy():
            if watcher in to_remove:
                logging.debug("Removing watcher for unload %r", watcher)
                self.watchers.remove(watcher)
        aliases_to_remove = []
        for name, command in self.commands.copy().items():
            if command in to_remove:
                logging.debug("Removing command for unload %r", command)
                del self.commands[name]
                aliases_to_remove.append(name)
        for alias, command in self.aliases.copy().items():
            if command in aliases_to_remove:
                del self.aliases[alias]
        return worked

    def add_alias(self, alias, cmd):
        """Make an alias"""
        if cmd not in self.commands.keys():
            return False
        self.aliases[alias.lower().strip()] = cmd
        return True

    def remove_alias(self, alias):
        """Remove an alias"""
        try:
            del self.aliases[alias.lower().strip()]
        except KeyError:
            return False
        return True

    async def log(self, type, *, group=None, affected_uids=None, data=None):
        return await asyncio.gather(*[fun(type, group, affected_uids, data) for fun in self._log_handlers])

    def register_logger(self, logger):
        self._log_handlers.append(logger)
