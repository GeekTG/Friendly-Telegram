from .. import loader
import logging

def register(cb):
    logging.info('Registering %s', __file__)
    cb(HelpMod())

class HelpMod(loader.Module):
    def __init__(self):
        logging.debug('%s started', __file__)
        self.commands = {'help':self.helpcmd}
        self.config = {}
        self.name = "HelpMod"
    async def helpcmd(self, message):
        reply = "```Available Modules:\n"
        for mod in loader.Modules.modules:
            reply += "\n  {} has {} {} available\n".format(mod.name, len(mod.commands), 'command' if len(mod.commands) == 1 else 'commands')
            for cmd in mod.commands:
                reply += "    {}\n".format(cmd)
        reply += "```"
        await message.edit(reply)

