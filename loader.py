import importlib, os, logging, sys
from . import config

class Module():
    def __init__(self):
        self.name = name
        self.instance = instance
        self.help = help
    def handle_command(self, message):
        logging.error("NI! %s", __func__)
    def get_help(self):
        logging.error("NI! %s", __func__)
    def get_name(self):
        logging.error("NI! %s", __func__)


class Modules():
    def __init__(self):
        self.commands = {}
        self.modules = []
    def register_all(self):
        print(os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), config.MODULES_NAME)))
        mods = filter(lambda x: (len(x) > 3 and x[-3:] == '.py'), os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), config.MODULES_NAME)))
        logging.debug(mods)
        print('mods')
        for mod in mods:
            mod = mod[:-3]
            importlib.import_module('.'+config.MODULES_NAME+'.'+mod, __package__)
            mod = __package__+'.'+config.MODULES_NAME+'.'+mod
            sys.modules[mod].register(self.register_cb)
            del sys.modules[mod]

    def register_cb(self, instance):
        if not issubclass(instance.__class__, Module):
            logging.error("Not a subclass %s", repr(instance.__class__))
        for command in instance.commands:
            if command in self.commands.keys():
                logging.error("Duplicate command %s", command)
                return False
            self.commands.update({command: instance.commands[command]})
        self.modules += [instance]
    def dispatch(self, command, message):
        logging.debug(self.commands)
        for com in self.commands:
            logging.debug(com)
            if command == '.'+com:
                logging.debug('found command')
                return self.commands[com](message) # Returns a coroutine.
