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
import importlib
import sys
import uuid
import asyncio

from importlib.machinery import ModuleSpec
from importlib.abc import SourceLoader

from .. import loader, utils
from ..compat import uniborg

import requests

logger = logging.getLogger(__name__)


def register(cb):
    cb(LoaderMod())


class StringLoader(SourceLoader):
    def __init__(self, data):
        self.data = data

    def get_filename(self, fullname):
        return "<string>"  # We really don't care

    def get_data(self, filename):
        return self.data


class LoaderMod(loader.Module):
    """Loads modules"""
    def __init__(self):
        self.name = _("Loader")
        self.config = loader.ModuleConfig("MODULES_REPO",
                                          "https://raw.githubusercontent.com/friendly-telegram/modules-repo/master",
                                          "Fully qualified URL to a module repo")
        self.allmodules = None
        self._pending_setup = []

    async def dlmodcmd(self, message):
        """Downloads and installs a module from the official module repo"""
        args = utils.get_args(message)
        if len(args) == 0:
            text = utils.escape_html("\n".join(await self.get_repo_list()))
            await utils.answer(message, "<b>" + _("Available official modules from repo")
                               + "</b>\n<code>" + text + "</code>")
        elif len(args) == 1:
            if await self.download_and_install_official(args[0], message):
                self._db.set(__name__, "loaded_modules",
                             list(set(self._db.get(__name__, "loaded_modules", []) + [args[0]])))

    async def get_repo_list(self):
        r = await utils.run_sync(requests.get, self.config["MODULES_REPO"] + "/manifest.txt")
        r.raise_for_status()
        return r.text.split("\n")

    async def download_and_install_official(self, module_name, message=None):
        url = self.config["MODULES_REPO"] + "/" + module_name + ".py"
        r = await utils.run_sync(requests.get, url)
        if r.status_code == 404:
            if message is not None:
                await message.edit(_("<b>Module not available in repo.</b>"))
            return False
        r.raise_for_status()
        return await self.load_module(r.content, message, url)

    async def loadmodcmd(self, message):
        """Loads the module file"""
        if message.file:
            msg = message
        else:
            msg = (await message.get_reply_message())
        if msg is None or msg.media is None:
            args = utils.get_args(message)
            if len(args) == 1:
                try:
                    path = args[0]
                    with open(path, "rb") as f:
                        doc = f.read()
                except FileNotFoundError:
                    await message.edit(_("<code>File not found</code>"))
                    return
            else:
                await message.edit(_("<code>Provide a module to load</code>"))
                return
        else:
            path = None
            doc = await msg.download_media(bytes)
        logger.debug("Loading external module...")
        try:
            doc = doc.decode("utf-8")
        except UnicodeDecodeError:
            await message.edit(_("<code>Invalid Unicode formatting in module</code>"))
            return
        if path is not None:
            await self.load_module(doc, message, path)
        else:
            await self.load_module(doc, message)

    async def load_module(self, doc, message, source="<string>"):
        uid = str(uuid.uuid4())
        module_name = "friendly-telegram.modules.__extmod_" + uid
        try:
            module = importlib.util.module_from_spec(ModuleSpec("friendly-telegram.modules.__extmod_" + uid,
                                                                StringLoader(doc), origin=source))
            module.borg = uniborg.UniborgClient()
            module._ = _
            sys.modules[module_name] = module
            module.__spec__.loader.exec_module(module)
        except Exception:  # That's okay because it might try to exit or something, who knows.
            logger.exception("Loading external module failed.")
            if message is not None:
                await message.edit(_("<code>Loading failed. See logs for details</code>"))
            return False
        if "register" not in vars(module):
            if message is not None:
                await message.edit(_("<code>Module did not expose correct API"))
            logging.error("Module does not have register(), it has " + repr(vars(module)))
            return False
        try:
            try:
                module.register(self.register_and_configure, module_name)
            except TypeError:
                module.register(self.register_and_configure)
            await self._pending_setup.pop()
        except Exception:
            if message is not None:
                await message.edit(_("<code>Module crashed.</code>"))
            return False
        if message is not None:
            await message.edit(_("<code>Module loaded.</code>"))
        return True

    def register_and_configure(self, instance):
        self.allmodules.register_module(instance)
        self.allmodules.send_config_one(instance, self._db)
        self._pending_setup.append(instance.client_ready(self._client, self._db))

    async def unloadmodcmd(self, message):
        """Unload module by class name"""
        args = utils.get_args(message)
        if len(args) != 1:
            await message.edit(_("<code>What class needs to be unloaded?</code>"))
            return
        clazz = args[0]
        worked = self.allmodules.unload_module(clazz)
        if worked:
            await message.edit(_("<code>Module unloaded.</code>"))
        else:
            await message.edit(_("<code>Nothing was unloaded.</code>"))

    async def _update_modules(self):
        todo = self._db.get(__name__, "loaded_modules", [])
        if todo is None:
            return  # User manually requested that we don't load core modules
        if len(todo) == 0:
            todo = await self.get_repo_list()
        await asyncio.gather(*[self.download_and_install_official(mod) for mod in todo])

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        await self._update_modules()
