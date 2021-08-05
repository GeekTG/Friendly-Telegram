#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2021 The Authors

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

#    Modded by GeekTG Team
#    Backup authors: @mishase, @tshipenchko

import asyncio
import importlib
import inspect
import io
import logging
import os
import re
import sys
import urllib
import uuid
import zlib
from importlib.abc import SourceLoader
from importlib.machinery import ModuleSpec
from os import path

import requests

from .. import loader, utils

logger = logging.getLogger(__name__)

VALID_URL = r"[-[\]_.~:/?#@!$&'()*+,;%<=>a-zA-Z0-9]+"
VALID_PIP_PACKAGES = re.compile(r"^\s*# requires:(?: ?)((?:{url} )*(?:{url}))\s*$".format(url=VALID_URL), re.MULTILINE)
USER_INSTALL = "PIP_TARGET" not in os.environ and "VIRTUAL_ENV" not in os.environ
GIT_REGEX = re.compile(r"^https?://github\.com((?:/[a-z0-9-]+){2})(?:/tree/([a-z0-9-]+)((?:/[a-z0-9-]+)*))?/?$",
                       flags=re.IGNORECASE)
fname = "ModulesBackup.bin"
enc = "utf-8"
d = [b"\xFD", b"\xFF"]


class StringLoader(SourceLoader):  # pylint: disable=W0223 # False positive, implemented in SourceLoader
    """Load a python module/file from a string"""

    def __init__(self, data, origin):
        self.data = data.encode("utf-8") if isinstance(data, str) else data
        self.origin = origin

    def get_code(self, fullname):
        source = self.get_source(fullname)
        if source is None:
            return None
        return compile(source, self.origin, "exec", dont_inherit=True)

    def get_filename(self, fullname):
        return self.origin

    def get_data(self, filename):  # pylint: disable=W0221,W0613
        # W0613 is not fixable, we are overriding
        # W0221 is a false positive assuming docs are correct
        return self.data


def unescape_percent(text):
    i = 0
    ln = len(text)
    is_handling_percent = False
    out = ""
    while i < ln:
        char = text[i]
        if char == "%" and not is_handling_percent:
            is_handling_percent = True
            i += 1
            continue
        if char == "d" and is_handling_percent:
            out += "."
            is_handling_percent = False
            i += 1
            continue
        out += char
        is_handling_percent = False
        i += 1
    return out


def get_git_api(url):
    m = GIT_REGEX.search(url)
    if m is None:
        return None
    repo = m.group(1)  # TODO: remove unused repo
    branch = m.group(2)
    path_ = m.group(3)
    api_url = "https://api.github.com/repos{}/contents".format(m.group(1))
    if path_ is not None and len(path_) > 0:
        api_url += path_
    if branch:
        api_url += "?ref=" + branch
    return api_url


@loader.tds
class LoaderMod(loader.Module):
    """Loads modules"""
    strings = {"name": "Loader",
               "repo_config_doc": "Fully qualified URL to a module repo",
               "avail_header": "<b>Available official modules from repo</b>",
               "select_preset": "<b>Please select a preset</b>",
               "no_preset": "<b>Preset not found</b>",
               "preset_loaded": "<b>Preset loaded</b>",
               "no_module": "<b>Module not available in repo.</b>",
               "no_file": "<b>File not found</b>",
               "provide_module": "<b>Provide a module to load</b>",
               "bad_unicode": "<b>Invalid Unicode formatting in module</b>",
               "load_failed": "<b>Loading failed. See logs for details</b>",
               "loaded": "<b>Module loaded.</b>",
               "no_class": "<b>What class needs to be unloaded?</b>",
               "unloaded": "<b>Module unloaded.</b>",
               "not_unloaded": "<b>Module not unloaded.</b>",
               "requirements_failed": "<b>Requirements installation failed</b>",
               "requirements_installing": "<b>Installing requirements...</b>",
               "requirements_restart": "<b>Requirements installed, but a restart is required</b>",
               "all_modules_deleted": "<b>All modules deleted</b>",
               "reply_to_txt": "<b>Reply to .txt file<b>",
               "restored_modules": "<b>Loaded:</b> <code>{}</code>\n<b>Already loaded:</b> <code>{}</code>",
               "backup_completed": "<b>Modules backup completed</b>\n<b>Count:</b> <code>{}</code>",
               "no_modules": "<b>You have no custom modules!</b>",
               "no_name_module": "<b>Type module name in arguments</b>",
               "no_command_module": "<b>Type module command in arguments</b>",
               "command_not_found": "<b>Command was not found!</b>",
               "searching": "<b>Searching...</b>",
               "file": "<b>File of module {}:<b>",
               "module_link": "<a href=\"{}\">Link</a> for module {}: \n<code>{}</code>",
               "not_found_info": "Request to find module with name {} failed due to:",
               "not_found_c_info": "Request to find module with command {} failed due to:",
               "not_found": "<b>Module was not found</b>",
               "file_core": "<b>File of core module {}:</b>",
               "loading": "<b>Loading...</b>",
               "url_invalid": "<b>URL invalid</b>",
               "args_incorrect": "<b>Args incorrect</b>",
               "repo_loaded": "<b>Repository loaded</b>",
               "repo_not_loaded": "<b>Repository not loaded</b>",
               "repo_unloaded": "<b>Repository unloaded, but restart is required to unload repository modules</b>",
               "repo_not_unloaded": "<b>Repository not unloaded</b>"}

    def __init__(self):
        super().__init__()
        self.config = loader.ModuleConfig("MODULES_REPO",
                                          "https://raw.githubusercontent.com/GeekTG/FTG-Modules/main/",
                                          lambda m: self.strings("repo_config_doc", m))

    @loader.owner
    async def dlmodcmd(self, message):
        """Downloads and installs a module from the official module repo"""
        args = utils.get_args(message)
        if args:
            args = args[0] if urllib.parse.urlparse(args[0]).netloc else args[0].lower()
            if await self.download_and_install(args, message):
                self._db.set(__name__, "loaded_modules",
                             list(set(self._db.get(__name__, "loaded_modules", [])).union([args])))
        else:
            text = utils.escape_html("\n".join(await self.get_repo_list("full")))
            await utils.answer(
                message,
                (
                    "<b>"
                    + self.strings("avail_header", message)
                    + "</b>\n"
                    + '\n'.join(
                        "<code>" + i + "</code>" for i in sorted(text.split('\n'))
                    )
                ),
            )

    @loader.owner
    async def dlpresetcmd(self, message):
        """Set preset. Defaults to full"""
        args = utils.get_args(message)
        if not args:
            await utils.answer(message, self.strings("select_preset", message))
            return
        try:
            await self.get_repo_list(args[0])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                await utils.answer(message, self.strings("no_preset", message))
                return
            raise
        self._db.set(__name__, "chosen_preset", args[0])
        self._db.set(__name__, "loaded_modules", [])
        self._db.set(__name__, "unloaded_modules", [])
        await utils.answer(message, self.strings("preset_loaded", message))
        await self.allmodules.commands["restart"](await message.reply("_"))

    async def _get_modules_to_load(self):
        todo = await self.get_repo_list(self._db.get(__name__, "chosen_preset", None))
        todo = todo.difference(self._db.get(__name__, "unloaded_modules", []))
        todo.update(self._db.get(__name__, "loaded_modules", []))
        return todo

    async def get_repo_list(self, preset=None):
        if preset is None:
            preset = "minimal"
        r = await utils.run_sync(requests.get, self.config["MODULES_REPO"] + "/" + preset + ".txt")
        r.raise_for_status()
        return set(filter(lambda x: x, r.text.split("\n")))

    async def download_and_install(self, module_name, message=None):
        if urllib.parse.urlparse(module_name).netloc:
            url = module_name
        else:
            url = self.config["MODULES_REPO"] + module_name + ".py"
        r = await utils.run_sync(requests.get, url)
        if r.status_code == 404:
            if message is not None:
                await utils.answer(message, self.strings("no_module", message))
            return False
        r.raise_for_status()
        return await self.load_module(r.content.decode("utf-8"), message, module_name, url)

    @loader.owner
    async def loadmodcmd(self, message):
        """Loads the module file"""
        msg = message if message.file else (await message.get_reply_message())
        if msg is None or msg.media is None:
            args = utils.get_args(message)
            if args:
                try:
                    path_ = args[0]
                    with open(path_, "rb") as f:
                        doc = f.read()
                except FileNotFoundError:
                    await utils.answer(message, self.strings("no_file", message))
                    return
            else:
                await utils.answer(message, self.strings("provide_module", message))
                return
        else:
            path_ = None
            doc = await msg.download_media(bytes)
        logger.debug("Loading external module...")
        try:
            doc = doc.decode("utf-8")
        except UnicodeDecodeError:
            await utils.answer(message, self.strings("bad_unicode", message))
            return
        if path_ is not None:
            await self.load_module(doc, message, origin=path_)
        else:
            await self.load_module(doc, message)

    async def load_module(self, doc, message, name=None, origin="<string>", did_requirements=False):
        if name is None:
            uid = "__extmod_" + str(uuid.uuid4())
        else:
            uid = name.replace("%", "%%").replace(".", "%d")
        module_name = "friendly-telegram.modules." + uid
        try:
            try:
                spec = ModuleSpec(module_name, StringLoader(doc, origin), origin=origin)
                instance = self.allmodules.register_module(spec, module_name)
            except ImportError:
                logger.info("Module loading failed, attemping dependency installation", exc_info=True)
                # Let's try to reinstall dependencies
                requirements = list(filter(lambda x: x and x[0] not in ("-", "_", "."),
                                           map(str.strip, VALID_PIP_PACKAGES.search(doc)[1].split(" "))))
                logger.debug("Installing requirements: %r", requirements)
                if not requirements:
                    raise  # we don't know what to install
                if did_requirements:
                    if message is not None:
                        await utils.answer(message, self.strings("requirements_restart", message))
                    return True  # save to database despite failure, so it will work after restart
                if message is not None:
                    await utils.answer(message, self.strings("requirements_installing", message))
                pip = await asyncio.create_subprocess_exec(sys.executable, "-m", "pip", "install",
                                                           "--upgrade", "-q", "--disable-pip-version-check",
                                                           "--no-warn-script-location",
                                                           *["--user"] if USER_INSTALL else [],
                                                           *requirements)
                rc = await pip.wait()
                if rc != 0:
                    if message is not None:
                        await utils.answer(message, self.strings("requirements_failed", message))
                    return False
                importlib.invalidate_caches()
                return await self.load_module(doc, message, name, origin, True)  # Try again
        except BaseException as e:  # That's okay because it might try to exit or something, who knows.
            logger.exception(f"Loading external module failed due to {e}")
            if message is not None:
                await utils.answer(message, self.strings("load_failed", message))
            return False
        try:
            self.allmodules.send_config_one(instance, self._db, self.babel)
            await self.allmodules.send_ready_one(instance, self._client, self._db, self.allclients)
        except Exception as e:
            logger.exception(f"Module threw because {e}")
            if message is not None:
                await utils.answer(message, self.strings("load_failed", message))
            return False
        if message is not None:
            await utils.answer(message, self.strings("loaded", message))
        return True

    @loader.owner
    async def dlrepocmd(self, message):
        """Downloads and installs all modules from repo"""
        args = utils.get_args(message)
        if len(args) == 1:
            repo_url = args[0]
            git_api = get_git_api(repo_url)
            if git_api is None:
                return await utils.answer(message, self.strings("url_invalid", message))
            await utils.answer(message, self.strings("loading", message))
            if await self.load_repo(git_api):
                self._db.set(__name__, "loaded_repositories",
                             list(set(self._db.get(__name__, "loaded_repositories", [])).union([repo_url])))
                await utils.answer(message, self.strings("repo_loaded", message))
            else:
                await utils.answer(message, self.strings("repo_not_loaded", message))
        else:
            await utils.answer(message, self.strings("args_incorrect", message))

    @loader.owner
    async def unloadrepocmd(self, message):
        """Removes loaded repository"""
        args = utils.get_args(message)
        if len(args) == 1:
            repoUrl = args[0]
            repos = set(self._db.get(__name__, "loaded_repositories", []))
            try:
                repos.remove(repoUrl)
            except KeyError:
                return await utils.answer(message, self.strings("repo_not_unloaded", message))
            self._db.set(__name__, "loaded_repositories", list(repos))
            await utils.answer(message, self.strings("repo_unloaded", message))
        else:
            await utils.answer(message, self.strings("args_incorrect", message))

    async def load_repo(self, git_api):
        req = await utils.run_sync(requests.get, git_api)
        if req.status_code != 200:
            return False
        files = req.json()
        if not isinstance(files, list):
            return False
        await asyncio.gather(*[self.download_and_install(f["download_url"]) for f in
                               filter(lambda f: f["name"].endswith(".py") and f["type"] == "file", files)])
        return True

    @loader.owner
    async def unloadmodcmd(self, message):
        """Unload module by class name"""
        args = utils.get_args(message)
        if not args:
            await utils.answer(message, self.strings("no_class", message))
            return
        clazz = ' '.join(args)
        worked = self.allmodules.unload_module(clazz.capitalize()) + self.allmodules.unload_module(clazz)
        without_prefix = []
        for mod in worked:
            assert mod.startswith("friendly-telegram.modules."), mod
            without_prefix += [unescape_percent(mod[len("friendly-telegram.modules."):])]
        it = set(self._db.get(__name__, "loaded_modules", [])).difference(without_prefix)
        self._db.set(__name__, "loaded_modules", list(it))
        it = set(self._db.get(__name__, "unloaded_modules", [])).union(without_prefix)
        self._db.set(__name__, "unloaded_modules", list(it))
        if worked:
            await utils.answer(message, self.strings("unloaded", message))
        else:
            await utils.answer(message, self.strings("not_unloaded", message))

    @loader.owner
    async def clearmodulescmd(self, message):
        """Delete all installed modules"""
        self._db.set("friendly-telegram.modules.loader", "loaded_modules", [])
        self._db.set("friendly-telegram.modules.loader", "unloaded_modules", [])
        await utils.answer(message, self.strings("all_modules_deleted", message))
        self._db.set(__name__, "chosen_preset", "none")
        await self.allmodules.commands["restart"](await message.reply("_"))

    @loader.owner
    async def backupcmd(self, message):
        """Backup all your modules"""
        modules = map(get_module, self.allmodules.modules)
        b = zlib.compress(d[1].join(
            map(lambda mod: d[0].join(map(lambda s: s if isinstance(s, bytes) else s.encode(enc), mod)),
                filter(lambda mod: None not in mod and mod[1] != "path", modules))))
        f = io.BytesIO(b)
        f.name = fname
        await message.client.send_file(message.to_id, f, caption=f"<b>Backup completed!</b>")
        await message.delete()

    @loader.owner
    async def restorecmd(self, message):
        """Restore modules from backup file"""
        reply = await message.get_reply_message()
        if not reply or not reply.file or not reply.file.name.endswith(".bin"):
            return await message.edit("<b>Reply to backup file</b>")
        await message.edit("<b>Downloading backup...</b>")
        f = io.BytesIO()
        await reply.download_media(f)
        f.seek(0)
        b = zlib.decompress(f.read())
        modules = list(map(lambda e: list(map(lambda x: x.decode(enc), e.split(d[0]))), b.split(d[1])))
        await message.edit("<b>Loading backup...</b>")
        for [_, mtype, data] in modules:
            if mtype == "link":
                if await self.download_and_install(data):
                    self._db.set(__name__, "loaded_modules",
                                 list(set(self._db.get(__name__, "loaded_modules", [])).union([data])))
            elif mtype == "text":
                await self.load_module(data, None)
        await message.edit("<b>Restore completed!</b>")

    @loader.owner
    async def moduleinfocmd(self, message):
        """Get link on module by one's command or name"""
        args = utils.get_args_raw(message).lower()
        if args.startswith(*self._db.get(__name__, "command_prefix", ["."])):
            args = args[1:]
            if not args:
                return await utils.answer(message, self.strings("no_command_module", message))
            if args in self.allmodules.commands.keys():
                args = self.allmodules.commands[args].__self__.strings["name"]
            elif args in self.allmodules.aliases.keys():
                args = self.allmodules.aliases[args]
                args = self.allmodules.commands[args].__self__.strings["name"]
            else:
                return await utils.answer(message, self.strings("command_not_found", message))
            message = await utils.answer(message, self.strings("searching", message))
            await self.send_module(message, args, False)
        else:
            args = utils.get_args_raw(message).lower()
            if not args:
                return await utils.answer(message, self.strings("no_name_module", message))
            message = await utils.answer(message, self.strings("searching", message))
            await self.send_module(message, args, True)

    async def send_module(self, message, args, by_name):
        """Sends module by name"""
        try:
            f = ' '.join(x.strings["name"] for x in self.allmodules.modules if
                         args.lower() == x.strings("name", message).lower())
            r = inspect.getmodule(
                next(filter(lambda x: args.lower() == x.strings("name", message).lower(), self.allmodules.modules)))
            link = r.__spec__.origin

            core_module = False

            if link.startswith("http"):
                text = self.strings("module_link", message).format(link, f, link)
            elif (
                not link.startswith("http")
                and link == "<string>"
                or not link.startswith("http")
                and link != "<string>"
                and not path.isfile(link)
            ):
                text = self.strings("file", message).format(f)
            else:
                core_module = True
                text = self.strings("file_core", message).format(f)
            if core_module:
                with open(link, "rb") as file:
                    out = io.BytesIO(file.read())
            else:
                out = io.BytesIO(r.__loader__.data)
            out.name = f + ".py"
            out.seek(0)

            await utils.answer(message, out, caption=text)
        except Exception as e:
            log_text = self.strings("not_found_info", message) if by_name else self.strings("not_found_info", message)
            logger.info(log_text.format(args) + f"\nDue to {e}", exc_info=True)
            await utils.answer(message, self.strings("not_found", message))

    async def _update_modules(self):
        todo = await self._get_modules_to_load()
        await asyncio.gather(*[self.download_and_install(mod) for mod in todo])
        repos = set(self._db.get(__name__, "loaded_repositories", []))
        await asyncio.gather(*[self.load_repo(get_git_api(url)) for url in repos])

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        await self._update_modules()


def get_module(module):
    name = module.name
    sysmod = sys.modules.get(module.__module__)
    origin = sysmod.__spec__.origin
    loader_ = sysmod.__loader__
    cname = type(loader_).__name__
    r = [name, None, None]
    if cname == "SourceFileLoader":
        r[1] = "path"
        r[2] = loader_.get_filename()
    elif cname == "StringLoader":
        if origin == "<string>":
            r[1] = "text"
            r[2] = loader_.data
        else:
            r[1] = "link"
            r[2] = origin
    return r
