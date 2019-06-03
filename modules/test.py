from .. import loader

def register(cb):
    cb(TestMod())

class TestMod(loader.Module):
    """Self-tests"""
    def __init__(self):
        self.commands = {'ping':self.pingcmd}
        self.config = {}
        self.name = "Tester"

    async def pingcmd(self, message):
        """Does nothing"""
        await message.edit('Pong')

