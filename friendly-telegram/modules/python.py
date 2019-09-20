# -*- coding: future_fstrings -*-

#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import ast
import traceback
import sys

from .. import loader, utils

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
    # This code saves __name__ and __package into a kwarg passed to the function.
    # It is set before the users code runs to make sure relative imports work
    global_args = "_globs"
    while global_args in globs.keys():
        # Make sure there's no name collision, just keep prepending _s
        global_args = "_" + global_args
    kwargs[global_args] = {}
    for glob in ["__name__", "__package__"]:
        # Copy data to args we are sending
        kwargs[global_args][glob] = globs[glob]

    root = ast.parse(code, "exec")
    code = root.body
    if isinstance(code[-1], ast.Expr):  # If we can use it as a lambda return (but multiline)
        code[-1] = ast.copy_location(ast.Return(code[-1].value), code[-1])  # Change it to a return statement
    # globals().update(**<global_args>)
    glob_copy = ast.Expr(ast.Call(func=ast.Attribute(value=ast.Call(func=ast.Name(id="globals", ctx=ast.Load()),
                                                                    args=[], keywords=[]),
                                                     attr="update", ctx=ast.Load()),
                                  args=[], keywords=[ast.keyword(arg=None,
                                                                 value=ast.Name(id=global_args, ctx=ast.Load()))]))
    glob_copy.lineno = 0
    glob_copy.col_offset = 0
    ast.fix_missing_locations(glob_copy)
    code.insert(0, glob_copy)
    args = []
    for a in list(map(lambda x: ast.arg(x, None), kwargs.keys())):
        a.lineno = 0
        a.col_offset = 0
        args += [a]
    fun = ast.AsyncFunctionDef("tmp", ast.arguments(args=[], vararg=None, kwonlyargs=args, kwarg=None, defaults=[],
                                                    kw_defaults=[None for i in range(len(args))]), code, [], None)
    fun.lineno = 0
    fun.col_offset = 0
    mod = ast.parse("")
    mod.body = [fun]
    comp = compile(mod, "<string>", "exec")

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
        self.name = _("Python")
        self.allmodules = None

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

    async def evalcmd(self, message):
        """.eval <expression>
           Evaluates python code"""
        ret = _("Evaluated expression:\n<code>{}</code>\nReturn value:\n<code>{}</code>")
        try:
            it = await meval(utils.get_args_raw(message), **await self.getattrs(message))
        except Exception:
            et, ei, tr = sys.exc_info()
            await message.edit(_("Failed to execute expression:\n<code>{}</code>\n\nDue to:\n<code>{}</code>")
                               .format(utils.escape_html(utils.get_args_raw(message)),
                               utils.escape_html("".join(traceback.format_exception(et, ei,
                                                                                    tr.tb_next.tb_next.tb_next)))))
            return
        ret = ret.format(utils.escape_html(utils.get_args_raw(message)), utils.escape_html(it))
        await utils.answer(message, ret)

    async def execcmd(self, message):
        """.aexec <expression>
           Executes python code"""
        try:
            await meval(utils.get_args_raw(message), **await self.getattrs(message))
        except Exception:
            et, ei, tr = sys.exc_info()
            await message.edit(_("Failed to execute expression:\n<code>{}</code>\n\nDue to:\n<code>{}</code>")
                               .format(utils.escape_html(utils.get_args_raw(message)),
                               utils.escape_html("".join(traceback.format_exception(et, ei,
                                                                                    tr.tb_next.tb_next.tb_next)))))
            return

    async def getattrs(self, message):
        return {"message": message, "client": self.client, "self": self, "db": self.db,
                "reply": await message.get_reply_message()}
