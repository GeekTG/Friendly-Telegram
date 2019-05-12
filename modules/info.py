from .. import loader
import logging
import subprocess
import platform


def register(cb):
    logging.info('Registering %s', __file__)
    cb(InfoMod())


class InfoMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'info': self.infocmd}
        self.config = {}
        self.name = "InfoMod"

    async def infocmd(self, message):
        kernelver = subprocess.run(['uname', '-r'], stdout=subprocess.PIPE)
        os = subprocess.run(['uname', '-o'], stdout=subprocess.PIPE)

        reply = "`System Info\nKernel: " + platform.release()
        reply += "\nArch: " + platform.architecture()[0]
        reply += "\nOS: " + platform.system()

        if platform.system() == 'Linux':
            a = open('/etc/os-release').readlines()
            b = {}
            for line in a:
                b[line.split('=')[0]] = line.split('=')[1].strip().strip('"')

            reply += "\nLinux Distribution: " + b["PRETTY_NAME"]
        reply += "\nMisc\n"
        reply += "Python version:" + platform.python_version()
        reply += '`'
        await message.edit(reply)
