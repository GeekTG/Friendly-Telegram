# -*- coding: future_fstrings -*-

import logging

from .. import loader, utils

from ast import *

logger = logging.getLogger(__name__)

def register(cb):
    cb(PythonMod())
# We dont modify locals VVVV ; this lets us keep the message available to the user-provided function
async def meval(code, **kwargs):
    # Note to self: please don't set globals here as they will be lost.
    # Don't clutter locals
    locs = {}
    # Restore globals later
    globs = globals().copy()
    # This code saves __name__ and __package into a kwarg passed to the function. It is set before the users code runs to make sure relative imports work
    global_args = "_globs"
    while global_args in globs.keys():
        # Make sure there's no name collision, just keep prepending _s
        global_args = "_"+global_args
    kwargs[global_args] = {}
    for glob in ["__name__", "__package__"]:
        # Copy data to args we are sending
        kwargs[global_args][glob] = globs[glob]

    root = parse(code, 'exec')
    code = root.body
    if isinstance(code[-1], Expr): # If we can use it as a lambda return (but multiline)
        code[-1] = copy_location(Return(code[-1].value), code[-1]) # Change it to a return statement
    args = []
    for a in list(map(lambda x: arg(x, None), kwargs.keys())):
        a.lineno = 0
        a.col_offset = 0
        args += [a]
    fun = AsyncFunctionDef('tmp', arguments(args=[], vararg=None, kwonlyargs=args, kwarg=None, defaults=[], kw_defaults=[None for i in range(len(args))]), code, [], None)
    fun.lineno = 0
    fun.col_offset = 0
    mod = Module([fun])
    comp = compile(mod, '<string>', 'exec')

    exec(comp, {}, locs)

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
        self.commands = {"eval":self.aevalcmd, "exec":self.aexeccmd}
        self.config = {}
        self.name = "Python"

    async def aevalcmd(self, message):
        """.eval <expression>
           Evaluates python code"""
        ret = "Evaluated expression <code>"
        ret += utils.escape_html(utils.get_args_raw(message))
        ret += "</code> and it returned <code>"
        ret += utils.escape_html(await meval(utils.get_args_raw(message), message=message, client=message.client))
        ret += "</code>"
        await message.edit(ret)

    async def aexeccmd(self, message):
        """.aexec <expression>
           Executes python code"""
        await meval(utils.get_args_raw(message), message=message, client=message.client)
