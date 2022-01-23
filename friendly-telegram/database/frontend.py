import asyncio
import json
import logging

class Database(dict):
    def __init__(self, backend, noop=False):
        super().__init__()
        self._backend = backend

    def __repr__(self):
        return object.__repr__(self)

    async def init(self):
        await self._backend.init(self.reload)
        db = await self._backend.do_download()
        if db is not None:
            try:
                self.update(**json.loads(db))
            except Exception:
                logging.error('Database load failed')
                raise


    async def close(self):
        try:
            await self.save()
        except Exception:
            logging.info("Database close failed", exc_info=True)
        if self._backend is not None:
            self._backend.close()

    def save(self):
        asyncio.ensure_future(self._backend.do_upload(json.dumps(self, indent=4, ensure_ascii=False)))

    def get(self, owner, key, default=None):
        try:
            return self[owner][key]
        except KeyError:
            return default

    def set(self, owner, key, value):
        super().setdefault(owner, {})[key] = value
        return self.save()

    async def reload(self, event):
        db = await self._backend.do_download()
        self.clear()
        self.update(**json.loads(db))

    async def store_asset(self, message):
        return await self._backend.store_asset(message)

    async def fetch_asset(self, message):
        return await self._backend.fetch_asset(message)

