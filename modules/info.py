from .. import loader, utils
import logging, subprocess, platform, asyncio, shutil

logger = logging.getLogger(__name__)

def register(cb):
    cb(InfoMod())


class InfoMod(loader.Module):
    """Provides system information about the computer hosting this bot"""
    def __init__(self):
        self.commands = {'info': self.infocmd}
        self.config = {}
        self.name = "Info"

    async def infocmd(self, message):
        reply = "<code>System Info\nKernel: " + utils.escape_html(platform.release())
        reply += "\nArch: " + utils.escape_html(platform.architecture()[0])
        reply += "\nOS: " + utils.escape_html(platform.system())

        if platform.system() == 'Linux':
            done = False
            try:
                a = open('/etc/os-release').readlines()
                b = {}
                for line in a:
                    b[line.split('=')[0]] = line.split('=')[1].strip().strip('"')
                reply += "\nLinux Distribution: " + utils.escape_html(b["PRETTY_NAME"])
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
                        reply += f"\nAndroid SDK: {sdks.decode('utf-8').strip()}\nAndroid Version: {vers.decode('utf-8').strip()}\nAndroid Security Patch: {secs.decode('utf-8').strip()}"
                        done = True
            if not done:
                reply += "\nCould not determine Linux distribution"
        reply += "\nPython version: " + utils.escape_html(platform.python_version())
        reply += '</code>'
        logger.debug(reply)
        await message.edit(reply, parse_mode="HTML")
