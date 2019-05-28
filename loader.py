import importlib, os, logging, sys, ast, asyncio

try:
    from . import config
except ImportError:
    from .. import config
class Module():
    def __init__(self):
        self.name = "Unknown"
        self.help = "Unknown"
        self.config = {}

    def config_complete(self):
        pass

    # Will always be called after config loaded.
    async def client_ready(self, client):
        pass

    async def handle_command(self, message):
        logging.error("NI! handle_command")

class Modules():
    instance = None
    @classmethod
    def get(clas):
        if not clas.instance:
            clas.instance = clas()
        return clas.instance
    commands = {}
    modules = []
    watchers = []

    def register_all(self):
        print(os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), MODULES_NAME)))
        mods = filter(lambda x: (len(x) > 3 and x[-3:] == '.py'), os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), MODULES_NAME)))
        logging.debug(mods)
        print('mods')
        for mod in mods:
            mod = mod[:-3] # Cut .py
            importlib.import_module('.'+MODULES_NAME+'.'+mod, __package__)
            mod = __package__+'.'+MODULES_NAME+'.'+mod
            sys.modules[mod].register(self.register_module)
            del sys.modules[mod]

    def register_module(self, instance):
        if not issubclass(instance.__class__, Module):
            logging.error("Not a subclass %s", repr(instance.__class__))
        for command in instance.commands:
            if command in self.commands.keys():
                logging.error("Duplicate command %s", command)
                continue
            self.commands.update({command: instance.commands[command]})
        try:
            if instance.watcher:
                self.watchers += [instance.watcher]
        except AttributeError:
            pass
        self.modules += [instance]


    def dispatch(self, command, message):
        logging.debug(self.commands)
        watchers = [watcher(message) for watcher in self.watchers]
        for com in self.commands:
            logging.debug(com)
            if command == '.'+com:
                logging.debug('found command')
                return asyncio.gather(self.commands[com](message), *watchers) # Returns a coroutine.

    def send_config(self, additional_config=None):
        for mod in self.modules:
            if hasattr(mod, "config"):
                for conf in mod.config.keys():
                    logging.debug(conf)
                    if conf in additional_config:
                        mod.config[conf] = ast.literal_eval(additional_config[conf])
                    elif hasattr(config, conf):
                        mod.config[conf] = getattr(config, conf)
                    else:
                        logging.warning("No config value for "+conf)
            logging.debug(mod.config)
            mod.config_complete()

    async def send_ready(self, client):
        for mod in self.modules:
            await mod.client_ready(client)
