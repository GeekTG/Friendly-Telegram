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

import json, asyncio

class Database():
    def __init__(self, backend):
        self._backend = backend
    async def init(self):
        await self._backend.init()
        db = await self._backend.do_download()
        if db != None:
            try:
                self._db = json.loads(db)
            except:
                # Don't worry if its corrupted. Just set it to {} and let it be fixed on next upload
                self._db = {}
        else:
            self._db = {}
    def get(self, owner, key, default=None):
        try:
            return self._db[owner][key]
        except KeyError:
            return default

    def set(self, owner, key, value):
        self._db.setdefault(owner, {})[key] = value
        asyncio.ensure_future(self._backend.do_upload(json.dumps(self._db)))
