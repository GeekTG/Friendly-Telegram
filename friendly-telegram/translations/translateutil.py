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

import ast
import os
import json

from .. import loader, utils


def ui():
    mods = filter(lambda x: (len(x) > 3 and x[-3:] == ".py"),
                  os.listdir(os.path.join(utils.get_base_dir(), loader.MODULES_NAME)))
    finder = UsageFinder()
    for mod in mods:
        with open(os.path.join(utils.get_base_dir(), loader.MODULES_NAME, mod), "r") as f:
            finder.visit(ast.parse(f.read()))
    output = finder.get_output()
    lang = input("Enter language code (two-character or underscore-seperated): ")
    filename = os.path.join(os.path.dirname(utils.get_base_dir()), "translations",
                            input("Enter translation pack name: "))
    translated = {}
    for string in output:
        tr = input("Translate `" + string + "` to " + lang + ": ")
        if len(tr.strip()) > 0:
            translated[string] = tr
    j = {lang: translated}
    with open(filename + ".json", "w") as file:
        json.dump(j, file)


class UsageFinder(ast.NodeVisitor):
    def __init__(self):
        self._output = []

    def visit_AsyncFunctionDef(self, node):
        self.generic_visit(node)
        self._output += [ast.get_docstring(node, clean=True)]

    def visit_Class(self, node):
        self.generic_visit(node)
        self._output += [ast.get_docstring(node, clean=True)]

    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == "_" and len(node.args) == 1:
            if len(node.keywords) == 0 and (isinstance(node.args[0], ast.Str)
                                            or (isinstance(node.args[0], ast.Constant)
                                                and isinstance(node.args[0].value, str))):
                self._output += [node.args[0].s]
            else:
                print("W: Could not process " + ast.dump(node))  # noqa: T001

    def get_output(self):
        return self._output
