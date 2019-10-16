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

import json
import asyncio


class NotifyingFuture(asyncio.Future):
    def __init__(self, *args, **kwargs):
        self.__to_notify_on_await = kwargs.pop("on_await", None)
        super().__init__(*args, **kwargs)

    def __await__(self):
        if callable(self.__to_notify_on_await):
            self.__to_notify_on_await()
        return super().__await__()


# Not thread safe, use the event loop!
class Database():
    def __init__(self, backend):
        self._noop = backend is None
        self._backend = backend
        self._pending = None
        self._loading = True
        self._waiter = asyncio.Event()
        self._sync_future = None
        # We use a future because we need await-ability and we will be delaying by 10s, but
        # because we are gonna frequently be changing the data, we want to avoid floodwait
        # and to do that we will discard most requests. However, attempting to await any request
        # should return a future corresponding to the next time that we flush the database.
        # To achieve this, we have one future stored here (the next time we flush the db) and we
        # always return that from set(). However, if someone decides to await set() much later
        # than when they called set(), it will already be finished. Luckily, we return a future,
        # not a reference to _sync_future, so it will be the correct future, and set_result will
        # already have been called. Simple, right?

    async def init(self):
        if self._noop:
            self._db = {}
            self._loading = False
            self._waiter.set()
            return
        await self._backend.init(self.reload)
        db = await self._backend.do_download()
        if db is not None:
            try:
                self._db = json.loads(db)
            except Exception:
                # Don't worry if its corrupted. Just set it to {} and let it be fixed on next upload
                self._db = {}
        else:
            self._db = {}
        self._loading = False
        self._waiter.set()

    def get(self, owner, key, default=None):
        try:
            return self._db[owner][key]
        except KeyError:
            return default

    def set(self, owner, key, value):
        if self._loading:
            self._waiter.wait()
        self._db.setdefault(owner, {})[key] = value
        if self._pending is not None and not self._pending.cancelled():
            self._pending.cancel()
        if self._sync_future is None or self._sync_future.done():
            self._sync_future = NotifyingFuture(on_await=self._cancel_then_set)
        self._pending = asyncio.ensure_future(_wait_then_do(10, self._set))  # Delay database ops by 10s
        return self._sync_future

    def _cancel_then_set(self):
        if self._pending is not None and not self._pending.cancelled():
            self._pending.cancel()
        self._pending = asyncio.ensure_future(self._set())
        # Restart the task, but without the delay, because someone is waiting for us

    async def _set(self):
        if self._noop:
            self._sync_future.set_result(True)
            return
        try:
            await self._backend.do_upload(json.dumps(self._db))
        except Exception as e:
            self._sync_future.set_exception(e)
        self._sync_future.set_result(True)

    async def reload(self, event):
        if self._noop:
            return
        try:
            self._waiter.clear()
            self._loading = True
            if self._pending is not None:
                self._pending.cancel()
            db = await self._backend.do_download()
            self._db = json.loads(db)
        finally:
            self._loading = False
            self._waiter.set()


async def _wait_then_do(time, task, *args, **kwargs):
    await asyncio.sleep(time)
    return await task(*args, **kwargs)
