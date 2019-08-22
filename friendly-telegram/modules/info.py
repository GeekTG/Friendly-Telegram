# -*- coding: future_fstrings -*-

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

from .. import loader, utils
import logging, subprocess, platform, asyncio, shutil

logger = logging.getLogger(__name__)

def register(cb):
    cb(InfoMod())


class InfoMod(loader.Module):
    """Provides system information about the computer hosting this bot"""
    def __init__(self):
        self.name = _("Info")

    async def infocmd(self, message):
        """Shows system information"""
        reply = "<code>" + _("System Info")
        reply += "\n" + _("Kernel: {}").format(utils.escape_html(platform.release()))
        reply += "\n" + _("Arch: {}").format(utils.escape_html(platform.architecture()[0]))
        reply += "\n" + _("OS: {}").format(utils.escape_html(platform.system()))

        if platform.system() == 'Linux':
            done = False
            try:
                a = open('/etc/os-release').readlines()
                b = {}
                for line in a:
                    b[line.split('=')[0]] = line.split('=')[1].strip().strip('"')
                reply += "\n" + _("Linux Distribution: {}").format(utils.escape_html(b["PRETTY_NAME"]))
                done = True
            except FileNotFoundError:
                getprop = shutil.which('getprop')
                if getprop != None:
                    sdk = await asyncio.create_subprocess_exec(getprop, 'ro.build.version.sdk', stdout=asyncio.subprocess.PIPE)
                    ver = await asyncio.create_subprocess_exec(getprop, 'ro.build.version.release', stdout=asyncio.subprocess.PIPE)
                    sec = await asyncio.create_subprocess_exec(getprop, 'ro.build.version.security_patch', stdout=asyncio.subprocess.PIPE)
                    sdks, _ = await sdk.communicate()
                    vers, _ = await ver.communicate()
                    secs, _ = await sec.communicate()
                    if sdk.returncode == 0 and ver.returncode == 0 and sec.returncode == 0:
                        reply += "\n" + _("Android SDK: {}").format(sdks.decode('utf-8').strip())
                        reply += "\n" + _("Android Version: {}").format(vers.decode('utf-8').strip())
                        reply += "\n" + _("Android Security Patch: {}").format(secs.decode('utf-8').strip())
                        done = True
            if not done:
                reply += "\n" + _("Could not determine Linux distribution")
        reply += "\n" + _("Python version: ").format(utils.escape_html(platform.python_version()))
        reply += '</code>'
        logger.debug(reply)
        await message.edit(reply)
