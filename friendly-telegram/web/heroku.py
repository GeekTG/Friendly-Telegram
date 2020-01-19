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

import atexit
import collections
import functools
import os

from .. import heroku


class Web:
    def __init__(self):
        super().__init__()
        if "heroku_api_token" in os.environ:
            # This is called before asyncio is even set up. We can only use sync methods which is fine.
            api_token = collections.namedtuple("api_token", ["ID", "HASH"])(os.environ["api_id"],
                                                                            os.environ["api_hash"])
            app, config = heroku.get_app([c[1] for c in self.client_data],
                                         os.environ["heroku_api_token"], api_token, False, True)
            if os.environ["DYNO"].startswith("web."):
                app.scale_formation_process("worker-DO-NOT-TURN-ON-OR-THINGS-WILL-BREAK", 0)
            atexit.register(functools.partial(exit_handler, app))


def exit_handler(app):
    app.scale_formation_process("worker-DO-NOT-TURN-ON-OR-THINGS-WILL-BREAK", 1)
