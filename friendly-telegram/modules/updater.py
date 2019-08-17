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
import logging, os, sys, atexit, asyncio, functools, random, git
from git import Repo

logger = logging.getLogger(__name__)

def register(cb):
    cb(UpdaterMod())


class UpdaterMod(loader.Module):
    """Updates itself"""
    def __init__(self):
        self.config = {"selfupdateid": -1, "selfupdatechat": -1, "selfupdatemsg": -1, "GIT_ORIGIN_URL": "https://github.com/penn5/friendly-telegram"}
        self.name = "Updater"

    async def restartcmd(self, message):
        """Restarts the userbot"""
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
        try:
            repo = Repo(os.path.dirname(utils.get_base_dir()))
            origin = repo.remote("origin")
            origin.pull()
        except git.exc.InvalidGitRepositoryError:
            repo = Repo.init(os.path.dirname(utils.get_base_dir()))
            origin = repo.create_remote("origin", self.config["GIT_ORIGIN_URL"])
            repo.create_head('master', origin.refs.master)
            repo.heads.master.set_tracking_branch(origin.refs.master)
            repo.heads.master.checkout()
        await message.edit("Downloaded! Use <code>.restart</code> to restart.")

    async def client_ready(self, client, db):
        self._me = await client.get_me()
        if self.config["selfupdateid"] == self._me.id:
            msg = "Restart successful!" if random.randint(0, 10) != 0 else "Restart failed successfully!"
            logger.debug("Self update successful! Edit message: "+str(self.config))
            await client.edit_message(self.config["selfupdatechat"], self.config["selfupdatemsg"], msg)

def restart(*args):
    os.execl(sys.executable, sys.executable, "-m", os.path.relpath(utils.get_base_dir()), *args)
