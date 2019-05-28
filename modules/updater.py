from .. import loader, utils, __main__
import logging, os, sys, atexit, functools, asyncio

def register(cb):
    logging.debug('Registering %s', __file__)
    cb(UpdaterMod())

class UpdaterMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'selfupdate': self.updatecmd, "pull": self.pullcmd}
        self.config = {"selfupdatechat": -1, "selfupdatemsg": -1, "GIT_PULL_COMMAND": ["git", "pull", "--ff-only"]}
        self.name = "Updater"
        self.help = "Provides self updates"

    async def updatecmd(self, message):
        await message.edit('Updating...')
        logging.debug("Self-update. " + sys.executable + "-m" + utils.get_base_dir())
        atexit.register(functools.partial(restart, "--config", "selfupdatechat", "--value", str(utils.get_chat_id(message)), "--config", "selfupdatemsg", "--value", str(message.id)))
        await message.client.disconnect()

    async def pullcmd(self, message):
        await message.edit("Downloading...")
        gitproc = await asyncio.create_subprocess_exec(*self.config["GIT_PULL_COMMAND"], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=utils.get_base_dir())
        out, err = await gitproc.communicate()
        if gitproc.returncode != 0:
            await message.edit("Error!\nStdout:\n<code>"+utils.escape_html(out.decode("utf-8"))+"</code>\nStderr:\n<code>"+utils.escape_html(err.decode("utf-8"))+"</code>", parse_mode="HTML")
        else:
            await message.edit("Downloaded!")
    async def client_ready(self, client):
        if self.config["selfupdatemsg"] >= 0:
            logging.debug("Self update successful! Edit message: "+str(self.config))
            await client.edit_message(self.config["selfupdatechat"], self.config["selfupdatemsg"], "Update successful!")

def restart(*args):
    os.execl(sys.executable, sys.executable, "-m", utils.get_base_dir(), *args)
