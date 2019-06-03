from .. import loader, utils
import logging, inspect

logger = logging.getLogger(__name__)

def register(cb):
    cb(HelpMod())

class HelpMod(loader.Module):
    """Provides this help message"""
    def __init__(self):
        self.commands = {'help':self.helpcmd}
        self.config = {}
        self.name = "Help"
    async def helpcmd(self, message):
        """.help [module]"""
        args = utils.get_args(message)
        if len(args) == 1:
            for mod in loader.Modules.modules:
                if mod.name == args[0]:
                    module = mod
            reply = f"<code>Help for {utils.escape_html(module.name)}:\n  "
            if module.__doc__:
                reply += utils.escape_html(inspect.cleandoc(module.__doc__))
            else:
                logging.warning("Module %s is missing docstring!", module)
            for name, fun in module.commands.items():
                reply += f"\n  {name}\n"
                if fun.__doc__:
                    reply += "\n".join(["    "+x for x in inspect.cleandoc(fun.__doc__).splitlines()])
                else:
                    reply += "There is no documentation for this command"
        else:
            reply = "<code>Available Modules:\n"
            for mod in loader.Modules.modules:
                reply += f"\n  {mod.name} has {len(mod.commands)} {'command' if len(mod.commands) == 1 else 'commands'} available\n"
                for cmd in mod.commands:
                    reply += f"    {cmd}\n"
        reply += "</code>"
        await message.edit(reply, parse_mode="HTML")

