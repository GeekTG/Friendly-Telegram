import json, asyncio

class Database():
    def __init__(self, backend):
        self._backend = backend
    async def init(self):
        await self._backend.init()
        db = await self._backend.do_download()
        if db != None:
            self._db = json.loads(db)
        else:
            self._db = {}
    def get(self, owner, key):
        return self._db[owner+"/"+key]
    def set(self, owner, key, value):
        self._db[owner+"/"+key] = value
        asyncio.create_task(self._backend.do_upload(json.dumps(self._db)))
