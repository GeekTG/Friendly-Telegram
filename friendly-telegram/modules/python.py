# -*- coding: future_fstrings -*-

import logging

from .. import loader, utils

logger = logging.getLogger(__name__)

def register(cb):
    cb(PythonMod())
# We dont modify locals VVVV ; this lets us keep the message available to the user-provided function
async def aexec(code, **kwargs):
    # Note to self: please don't set globals here as they will be lost.
    # Don't clutter locals
    locs = {}
    # Restore globals later
    globs = globals().copy()
    args = ", ".join(list(kwargs.keys()))
    exec(f"async def tmp({args}):\n    " + code.replace("\n", "\n    "), {}, locs)
    r = await locs["tmp"](**kwargs)
    try:
        globals().clear()
        # Inconsistent state
    finally:
        globals().update(**globs)
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
        ret += utils.escape_html(utils.get_args_raw(message))
        ret += "</code> and it returned <code>"
        ret += utils.escape_html(await utils.run_sync(eval, utils.get_args_raw(message), {}, {"message":message}))
        ret += "</code>"
        await message.edit(ret)
    async def aevalcmd(self, message):
        """.aeval <expression>
           Evaluates asyncronous python code"""
        ret = "Evaluated expression <code>"
        ret += utils.escape_html(utils.get_args_raw(message))
        ret += "</code> and it returned <code>"
        ret += utils.escape_html(await aexec(utils.get_args_raw(message), message=message))
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
#                  So we don't modify locals      VVVVV
        await aexec(utils.get_args_raw(message), message=message)
