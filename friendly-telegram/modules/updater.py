# -*- coding: future_fstrings -*-

from .. import loader, utils, __main__
import logging, os, sys, atexit, asyncio, functools, random

logger = logging.getLogger(__name__)

def register(cb):
    cb(UpdaterMod())


class UpdaterMod(loader.Module):
    """Updates itself"""
    def __init__(self):
        self.commands = {'restart': self.restartcmd, "download": self.downloadcmd}
        self.config = {"selfupdateid": -1, "selfupdatechat": -1, "selfupdatemsg": -1, "GIT_PULL_COMMAND": ["git", "pull", "--ff-only"]}
        self.name = "Updater"

    async def restartcmd(self, message):
        """Restarts the userbot"""
        logger.debug(message.client.phone)
        logger.debug(self._me)
        logger.debug(self.allclients)
        await message.edit('Restarting...')
        logger.debug("Self-update. " + sys.executable + " -m " + utils.get_base_dir())
        atexit.register(functools.partial(restart, "--config", "selfupdateid", "--value", str(self._me.id), "--config", "selfupdatechat", "--value", str(utils.get_chat_id(message)), "--config", "selfupdatemsg", "--value", str(message.id)))
        for client in self.allclients:
            # Terminate main loop of all running clients
            # Won't work if not all clients are ready
            if not client is message.client:
                await client.disconnect()
        await message.client.disconnect()

    async def downloadcmd(self, message):
        """Downloads userbot updates"""
        await message.edit("Downloading...")
        gitproc = await asyncio.create_subprocess_exec(*self.config["GIT_PULL_COMMAND"], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=utils.get_base_dir())
        out, err = await gitproc.communicate()
        if gitproc.returncode != 0:
            await message.edit("Error!\nStdout:\n<code>"+utils.escape_html(out.decode("utf-8"))+"</code>\nStderr:\n<code>"+utils.escape_html(err.decode("utf-8"))+"</code>")
        else:
            await message.edit("Downloaded! Use <code>.restart</code> to restart.")
    async def client_ready(self, client, db):
        self._me = await client.get_me()
        if self.config["selfupdateid"] == self._me.id:
            msg = "Restart successful!" if random.randint(0, 10) != 0 else "Restart failed successfully!"
            logger.debug("Self update successful! Edit message: "+str(self.config))
            await client.edit_message(self.config["selfupdatechat"], self.config["selfupdatemsg"], msg)

def restart(*args):
    os.execl(sys.executable, sys.executable, "-m", os.path.relpath(utils.get_base_dir()), *args)
