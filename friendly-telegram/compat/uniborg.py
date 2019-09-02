from .util import get_cmd_name, MarkdownBotPassthrough
from .. import loader

from functools import wraps

import logging
import telethon
import sys
import re

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

            self._module = func.__module__
            sys.modules[self._module].__dict__["register"] = self.registerfunc
            sys.modules[self._module].__dict__["borg"] = self
            sys.modules[self._module].__dict__["logger"] = logging.getLogger(self._module)
            sys.modules[self._module].__dict__["storage"] = self._storage

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

                        return func(event2)
                        # Return a coroutine
                    else:
                        logger.debug("but not matched cmd " + message.message
                                     + " regex " + event.pattern.__self__.pattern)
                self._commands[cmd] = commandhandler
            elif event.incoming:
                @wraps(func)
                def watcherhandler(message):
                    """Closure to execute watcher when handler activated and regex matched"""
                    match = re.match(event.pattern.__self__.pattern, "." + message.message, re.I)
                    if match:
                        logger.debug("and matched")
                        message.message = "." + message.message  # Framework strips prefix, give them a generic one
                        event2 = MarkdownBotPassthrough(message)
                        # Try to emulate the expected format for an event
                        event2.text = list(str(message.message))
                        event2.pattern_match = match
                        event2.message = MarkdownBotPassthrough(message)

                        return func(event2)
                        # Return a coroutine
                self._watchers += [watcherhandler]  # Add to list of watchers so we can call later.
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
