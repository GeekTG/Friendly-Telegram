from .. import loader, utils, __main__
import logging, os, sys, atexit, functools, asyncio

logger = logging.getLogger(__name__)

def register(cb):
    cb(UpdaterMod())

class UpdaterMod(loader.Module):
    """Updates itself"""
    def __init__(self):
        self.commands = {'selfupdate': self.updatecmd, "pull": self.pullcmd}
        self.config = {"selfupdatechat": -1, "selfupdatemsg": -1, "GIT_PULL_COMMAND": ["git", "pull", "--ff-only"]}
        self.name = "Updater"

    async def updatecmd(self, message):
        """Restarts the userbot"""
        await message.edit('Updating...')
        logger.debug("Self-update. " + sys.executable + "-m" + utils.get_base_dir())
        atexit.register(functools.partial(restart, "--config", "selfupdatechat", "--value", str(utils.get_chat_id(message)), "--config", "selfupdatemsg", "--value", str(message.id)))
        await message.client.disconnect()

    async def pullcmd(self, message):
        """Downloads userbot updates"""
        await message.edit("Downloading...")
        gitproc = await asyncio.create_subprocess_exec(*self.config["GIT_PULL_COMMAND"], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=utils.get_base_dir())
        out, err = await gitproc.communicate()
        if gitproc.returncode != 0:
            await message.edit("Error!\nStdout:\n<code>"+utils.escape_html(out.decode("utf-8"))+"</code>\nStderr:\n<code>"+utils.escape_html(err.decode("utf-8"))+"</code>", parse_mode="HTML")
        else:
            await message.edit("Downloaded! Use <code>.selfupdate</code> to restart.", parse_mode="HTML")
    async def client_ready(self, client, db):
        if self.config["selfupdatemsg"] >= 0:
            logger.debug("Self update successful! Edit message: "+str(self.config))
            await client.edit_message(self.config["selfupdatechat"], self.config["selfupdatemsg"], "Update successful!")

def restart(*args):
    os.execl(sys.executable, sys.executable, "-m", utils.get_base_dir(), *args)
