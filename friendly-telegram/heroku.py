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

from . import utils
import heroku3, logging, json, os
from git import Repo

def publish(clients, key, api_token=None):
    data = json.dumps({getattr(client, "phone", ""): client.session.save() for client in clients})
    heroku = heroku3.from_key(key)
    logging.debug("Configuring heroku...")
    app = None
    for poss_app in heroku.apps():
        config = poss_app.config()
        if (api_token is None or (config["api_id"] == api_token.ID and config["api_hash"] == api_token.HASH)) and config["authorization_strings"] == data:
            app = poss_app
            break
    if not app:
        app = heroku.create_app(stack_id_or_name='heroku-18', region_id_or_name="us")
    config = app.config()
    config["authorization_strings"] = data
    config["heroku_api_token"] = key
    if api_token is not None:
        config["api_id"] = api_token.ID
        config["api_hash"] = api_token.HASH
    repo = get_repo()
    url = app.git_url.replace("https://", "https://api:" + key + "@")
    if "heroku" in repo.remotes:
        remote = repo.remote("heroku")
        remote.set_url(url)
    else:
        remote = repo.create_remote("heroku", url)
    print("Pushing...")
    remote.push(refspec='HEAD:refs/heads/master')
    print("Pushed")

def get_repo():
    try:
        repo = Repo(os.path.dirname(utils.get_base_dir()))
    except git.exc.InvalidGitRepositoryError:
        repo = Repo.init(os.path.dirname(utils.get_base_dir()))
        origin = repo.create_remote("origin", self.config["GIT_ORIGIN_URL"])
        origin.fetch()
        repo.create_head('master', origin.refs.master)
        repo.heads.master.set_tracking_branch(origin.refs.master)
        repo.heads.master.checkout(True)
    return repo
