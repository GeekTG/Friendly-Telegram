# flake8: noqa: I didnt finish coding it lol

from .util import get_cmd_name, MarkdownBotPassthrough

from functools import wraps
from inspect import signature

import logging
import telethon

logger = logging.getLogger(__name__)

class UniborgClient:
    class __UniborgShimMod__Base(loader.Module):
        def __init__(self, borg):
            self._borg = borg
            self.commands = borg._commands
            self.name = "UniborgShim__" + borg._module

        async def watcher(self, message):
            for w in self._borg._watchers:
                w(message)
    def registerfunc(self, cb):
        cb(type("__UniborgShimMod__" + self._module, (self.__UniborgShimMod__Base,), dict())(self))

    def __init__(self):
        self._storage = None  # TODO

    def on(self, event):
        def subreg(func):
            logger.debug(event)
            sig = signature(func)
            newsig = sig.replace(parameters=tuple(sig.parameters) + (Parameter("borg", KEYWORD_ONLY),
                                                                     Parameter("logger", KEYWORD_ONLY),
                                                                     Parameter("storage", KEYWORD_ONLY)))
            logger.debug(newsig)
            func.__signature__ = newsig

            self._module = func.__module__

            sys.modules[self._module].__dict__["register"] = self.registerfunc
            sys.modules[self._module].

            if event.outgoing:
                # Command based thing
                if not event.pattern:
                    logger.error("Unable to register for outgoing messages without pattern.")
                    return func
                cmd = get_cmd_name(event.pattern)
                if not cmd:
                    return func

                @wraps(func)
                def commandhandler(message):
                    """Closure to execute command when handler activated and regex matched"""
                    logger.debug("Command triggered")
                    match = re.match(event.pattern, message.message, re.I)
                    if match:
                        logger.debug("and matched")
                        message.message = "." + message.message  # Framework strips prefix, give them a generic one
                        event = MarkdownBotPassthrough(message)
                        # Try to emulate the expected format for an event
                        event.text = list(str(message.message))
                        event.pattern_match = match
                        event.message = MarkdownBotPassthrough(message)
                        # TODO storage
                        return func(event, borg=event.client, logger=logging.getLogger(func.__module__), storage=self._storage)
                        # Return a coroutine
                    else:
                        logger.debug("but not matched cmd " + message.message + " regex " + kwargs["pattern"])
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


class UniborgUtil:
    def __init__(self, clients):
        pass

    def admin_cmd(self, **kwargs):
        """Uniborg uses this for sudo users but we don't have that concept."""
        return telethon.events.NewMessage(**kwargs)
