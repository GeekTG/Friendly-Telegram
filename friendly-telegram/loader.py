import importlib, os, logging, sys, ast, asyncio
MODULES_NAME="modules"

class Module():
    """There is no help for this module"""
    def __init__(self):
        self.name = "Unknown"
        self.config = {}

    def config_complete(self):
        pass

    # Will always be called after config loaded.
    async def client_ready(self, client, db):
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

    def register_all(self, skip):
        logging.debug(os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), MODULES_NAME)))
        mods = filter(lambda x: (len(x) > 3 and x[-3:] == '.py'), os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), MODULES_NAME)))
        logging.debug(mods)
        for mod in mods:
            mod = mod[:-3] # Cut .py
            try:
                importlib.import_module('.'+MODULES_NAME+'.'+mod, __package__)
                mod = __package__+'.'+MODULES_NAME+'.'+mod # FQN
                if mod in skip:
                    logging.debug("Not loading module %s because it is blacklisted", mod)
                    continue
                sys.modules[mod].register(self.register_module)
            except BaseException as e:
                logging.exception("Failed to load module %s due to:", mod)
            finally:
                try:
                    del sys.modules[mod]
                except BaseException as e:
                    logging.exception("Failed to clear namespace of module %s due to:", mod)
                    pass

    def register_module(self, instance):
        if not issubclass(instance.__class__, Module):
            logging.error("Not a subclass %s", repr(instance.__class__))
        for command in instance.commands:
            if command.lower() in self.commands.keys():
                logging.error("Duplicate command %s", command)
                continue
            if not instance.commands[command].__doc__:
                logging.warning("Missing docs for %s", command)
            self.commands.update({command.lower(): instance.commands[command]})
        try:
            if instance.watcher:
                self.watchers += [instance.watcher]
        except AttributeError:
            pass
        self.modules += [instance]


    def dispatch(self, command, message):
        logging.debug(self.commands)
        for com in self.commands:
            logging.debug(com)
            if command.lower() == "."+com:
                logging.debug('found command')
                return self.commands[com](message) # Returns a coroutine

    def send_config(self, db, additional_config=None):
        for mod in self.modules:
            if hasattr(mod, "config"):
                modcfg = db.get(mod.__module__, "__config__", {})
                logging.debug(modcfg)
                for conf in mod.config.keys():
                    logging.debug(conf)
                    if conf in additional_config:
                        mod.config[conf] = ast.literal_eval(additional_config[conf])
                    elif conf in modcfg.keys():
                        mod.config[conf] = modcfg[conf]
                    else:
                        logging.debug("No config value for "+conf)
            logging.debug(mod.config)
            try:
                mod.config_complete()
            except:
                logging.exception("Failed to send mod config complete signal")

    async def send_ready(self, client, db):
        try:
            await asyncio.gather(*[m.client_ready(client, db) for m in self.modules])
        except:
            logging.exception("Failed to send mod init complete signal")
