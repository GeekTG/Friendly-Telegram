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
    def get(self, owner, key):
        try:
            return self._db[owner][key]
        except KeyError:
            return None

    def set(self, owner, key, value):
        self._ensure_owned(owner)
        self._db[owner][key] = value
        asyncio.ensure_future(self._backend.do_upload(json.dumps(self._db)))
    def _ensure_owned(self, owner):
        if not owner in self._db.keys():
            self._db[owner] = {}
