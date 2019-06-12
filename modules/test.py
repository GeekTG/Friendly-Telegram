from .. import loader, utils

def register(cb):
    cb(TestMod())

class TestMod(loader.Module):
    """Self-tests"""
    def __init__(self):
        self.commands = {'ping':self.pingcmd, 'dump':self.dumpcmd}
        self.config = {}
        self.name = "Tester"

    async def pingcmd(self, message):
        """Does nothing"""
        await message.edit('Pong')

    async def dumpcmd(self, message):
        """Use in reply to get a dump of a message"""
        if not message.is_reply:
            return
        await message.edit(utils.escape_html((await message.get_reply_message()).stringify()), parse_mode="HTML")
