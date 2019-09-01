# flake8: noqa: I utterly gave up and killed myself. 

from .util import get_cmd_name, MarkdownBotPassthrough
from .. import loader

from functools import wraps
from inspect import signature, Parameter

import logging
import telethon
import sys
import re
import types

logger = logging.getLogger(__name__)

class UniborgClient:
    class __UniborgShimMod__Base(loader.Module):
        def __init__(self, borg):
            self._borg = borg
            self.commands = borg._commands
            print(self.commands)
            self.name = "UniborgShim__" + borg._module

        async def watcher(self, message):
            for w in self._borg._watchers:
                w(message)
    def registerfunc(self, cb):
        cb(type("__UniborgShimMod__" + self._module, (self.__UniborgShimMod__Base,), dict())(self))

    def __init__(self):
        self._storage = None  # TODO
        self._commands = {}
        self._watchers = []

    def on(self, event):
        def subreg(func):
            logger.debug(event)
            sig = signature(func)
            logger.debug(sig)

            self._module = func.__module__
            sys.modules[self._module].__dict__["register"] = self.registerfunc

            if event.outgoing:
                # Command based thing
                if not event.pattern:
                    logger.error("Unable to register for outgoing messages without pattern.")
                    return func
                cmd = get_cmd_name(event.pattern.__self__.pattern)
                if not cmd:
                    return func

                @wraps(func)
                def commandhandler(message):
                    """Closure to execute command when handler activated and regex matched"""
                    logger.debug("Command triggered")
                    match = re.match(event.pattern.__self__.pattern, "." + message.message, re.I)
                    if match:
                        logger.debug("and matched")
                        message.message = "." + message.message  # Framework strips prefix, give them a generic one
                        event2 = MarkdownBotPassthrough(message)
                        # Try to emulate the expected format for an event
                        event2.text = list(str(message.message))
                        event2.pattern_match = match
                        event2.message = MarkdownBotPassthrough(message)
                        # TODO storage

                        import dis
                        co = func.__code__
                        logger.debug(co.co_varnames)
                        logger.debug(co.co_names)
                        logger.debug(co.co_code)
                        dis.dis(co)

                        LOAD_GLOBAL = b't'
                        STORE_FAST = b'}'
                        inject_code = LOAD_GLOBAL  # Load global var passed via eval()
                        inject_code += bytes([len(co.co_names)])  # Set it to one higher than the final global
                        inject_code += STORE_FAST  # Store...
                        inject_code += bytes([0])  # ... to 0th local, which is the param
                        dis.dis(inject_code)
#                        inject_names = (co.co_varnames[0],)
                        inject_names = ("__event__",)

                        code = types.CodeType(co.co_argcount - 1,  # Remove the argument
                                              co.co_kwonlyargcount,
                                              co.co_nlocals,
                                              co.co_stacksize,
                                              co.co_flags,
                                              inject_code + co.co_code,
                                              co.co_consts,
                                              co.co_names + inject_names,
                                              co.co_varnames,
                                              co.co_filename,
                                              co.co_name,
                                              co.co_firstlineno,
                                              co.co_lnotab,
                                              co.co_freevars,
                                              co.co_cellvars)
                        dis.dis(code)
                        dis.show_code(code)

                        globs = vars(sys.modules[func.__module__])  # Keep context
                        # Pass params as locals because its genuinely the cleanest way
#                        params = {list(sig.parameters.keys())[0]: event2}
                        params = {"__event__": event2}
                        params.update(borg=event2.client)
                        params.update(logger=logging.getLogger(func.__module__))
                        params.update(storage=self._storage)
                        logger.debug(params)
                        globs.update(params)
                        return eval(code, globs, params)
                        # Return a coroutine
                    else:
                        logger.debug("but not matched cmd " + message.message + " regex " + event.pattern.__self__.pattern)
                self._commands[cmd] = commandhandler
            elif event.incoming:
                @wraps(func)
                def watcherhandler(message):
                    """Closure to execute watcher when handler activated and regex matched"""
                    match = re.match(message.message, kwargs.get("pattern", ".*"), re.I)
                    if match:
                        event = message
                        # Try to emulate the expected format for an event
                        event = MarkdownBotPassthrough(message)
                        # Try to emulate the expected format for an event
                        event.text = list(str(message.message))
                        event.pattern_match = match
                        event.message = MarkdownBotPassthrough(message)
                        return func(event)  # Return a coroutine
                self._watchers += [subwatcher]  # Add to list of watchers so we can call later.
            else:
                logger.error("event not incoming or outgoing")
                return func
            return func
        return subreg


class Uniborg:
    def __init__(self, clients):
        self.__all__ = "util"

class UniborgUtil:
    def __init__(self, clients):
        pass

    def admin_cmd(self, **kwargs):
        """Uniborg uses this for sudo users but we don't have that concept."""
        return telethon.events.NewMessage(**kwargs)

# If you try to revive this code, careful not to die inside along the way
