# -*- coding: future_fstrings -*-

import logging

from .. import loader, utils

logger = logging.getLogger(__name__)

def register(cb):
    cb(PythonMod())
# We dont modify locals VVVV
async def aexec(code, message):
    # Note to self: please don't set globals here as they will be lost.
    l = {}
    g = globals().copy()
    exec("async def tmp(message):\n    " + code.replace("\n", "\n    "), {}, l)
    # Don't expect it to return from the coro.
    r = await l["tmp"](message)
    try:
        globals().clear()
        # Inconsistent state
    finally:
        globals().update(**g)
    return r
class PythonMod(loader.Module):
    """Python stuff"""
    def __init__(self):
        self.commands = {"eval":self.evalcmd, "aeval":self.aevalcmd, "exec":self.execcmd, "aexec":self.aexeccmd}
        self.config = {}
        self.name = "Python"

    async def evalcmd(self, message):
        """.eval <expression>
           Evaluates non-asyncronous python code"""
        ret = "Evaluated expression <code>"
        ret += utils.escape_html(message.message)
        ret += "</code> and it returned <code>"
        ret += utils.escape_html(await utils.run_sync(eval, utils.get_args_raw(message), globals(), locals()))
        ret += "</code>"
        await message.edit(ret)
    async def aevalcmd(self, message):
        """.aeval <expression>
           Evaluates asyncronous python code"""
        ret = "Evaluated expression <code>"
        ret += utils.escape_html(message.message)
        ret += "</code> and it returned <code>"
        ret += utils.escape_html(await aexec(utils.get_args_raw(message), message))
        ret += "</code>"
        await message.edit(ret)
    async def execcmd(self, message):
        """.exec <expression>
           Executes non-asyncronous python code"""
        # Do NOT edit the message, as thats one of few ways to get the message out
        exec(utils.get_args_raw(message), globals(), locals())

    async def aexeccmd(self, message):
        """.aexec <expression>
           Executes asyncronous python code"""
        logging.debug(utils.get_args_raw(message))
#                  So we don't modify locals      VVVVV
        await aexec(utils.get_args_raw(message), message)
