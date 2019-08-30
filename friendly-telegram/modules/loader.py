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

from importlib.machinery import ModuleSpec
from importlib.abc import SourceLoader

from .. import loader, utils

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
        self.allmodules = None

    async def loadmodcmd(self, message):
        """Loads the module file"""
        if message.file:
            msg = message
        else:
            msg = (await message.get_reply_message())
        if msg is None or msg.media is None:
            await message.edit(_("<code>Provide a module to load</code>"))
            return
        logger.debug("Loading external module...")
        doc = await msg.download_media(bytes)
        try:
            doc = doc.decode("utf-8")
        except UnicodeDecodeError:
            await message.edit(_("<code>Invalid Unicode formatting in module</code>"))
            return
        uid = str(uuid.uuid4())
        try:
            module = importlib.util.module_from_spec(ModuleSpec("friendly-telegram.modules.__extmod_" + uid,
                                                                StringLoader(doc), origin="<string>"))
            sys.modules["friendly-telegram.modules.__extmod_" + uid] = module
            module.__spec__.loader.exec_module(module)
        except BaseException:  # That's okay because it might try to exit or something, who knows.
            await message.edit(_("<code>Loading failed. See logs for details</code>"))
            logging.exception("Loading external module failed.")
            return
        if "register" not in vars(module):
            await message.edit(_("<code>Module did not expose correct API"))
            logging.error("Module does not have register(), it has " + repr(vars(module)))
            return
        vars(module)["register"](self.allmodules.register_module)  # Invoke generic registration

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
