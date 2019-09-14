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

import locale
import os
import inspect
import ast

from dialog import Dialog, ExecutableNotFound

from . import utils, main


class TDialog():
    OK = 0
    NOT_OK = 1

    # Similar interface to pythondialog
    def menu(self, title, choices):
        print()
        print()
        print(title)
        print()
        biggest = max([len(k) for k, d in choices])
        i = 1
        for k, d in choices:
            print(" " + str(i) + ". " + k + (" " * (biggest + 2 - len(k))) + (d.replace("\n", "...\n      ")))
            i += 1
        while True:
            inp = input("Please enter your selection as a number, or 0 to cancel: ")
            try:
                inp = int(inp)
                if inp == 0:
                    return (self.NOT_OK, "Cancelled")
                return (self.OK, choices[inp - 1][0])
            except (ValueError, IndexError):
                pass

    def inputbox(self, query):
        print()
        print()
        print(query)
        print()
        inp = input("Please enter your response, or type nothing to cancel: ")
        if inp == "":
            return (self.NOT_OK, "Cancelled")
        return (self.OK, inp)

    def msgbox(self, msg):
        print()
        print()
        print(msg)

    def set_background_title(self, x):
        pass

    def yesno(self, question):
        return input(question + "y/N").lower() == "y"


TITLE = ""

try:
    d = Dialog(dialog="dialog", autowidgetsize=True)
except ExecutableNotFound:
    # Fall back to a terminal based configurator.
    d = TDialog()

locale.setlocale(locale.LC_ALL, '')

global modules
global db  # eww... meh.


def validate_value(string):
    try:
        return ast.literal_eval(string)
    except Exception:
        return string


def modules_config():
    global db
    code, tag = d.menu(TITLE, choices=[(module.name, inspect.cleandoc(getattr(module, "__doc__", None) or ""))
                                       for module in modules.modules])
    if code == d.OK:
        for mod in modules.modules:
            if mod.name == tag:
                # Match
                choices = [("Enabled", "Set to 0 to disable this module, 1 to enable")]
                for key, value in getattr(mod, "config", {}).items():
                    if key.upper() == key:  # Constants only
                        choices += [(key, getattr(mod.config, "getdoc", lambda k: "")(key))]
                code, tag = d.menu(TITLE, choices=choices)
                if code == d.OK:
                    code, string = d.inputbox(tag)
                    if code == d.OK:
                        if tag == "Enabled":
                            try:
                                enabled = int(string) > 0
                            except ValueError:
                                enabled = True
                            try:
                                db.setdefault(main.__name__, {}).setdefault("disable_modules",
                                                                            []).remove(mod.__module__)
                            except ValueError:
                                pass
                            if not enabled:
                                db.setdefault(main.__name__, {}).setdefault("disable_modules",
                                                                            []).append(mod.__module__)
                        else:
                            db.setdefault(mod.__module__, {}).setdefault("__config__",
                                                                         {})[tag] = validate_value(string)
                modules_config()
                return
    else:
        return


def run(database, phone, init, mods):
    global db, modules, TITLE
    db = database
    modules = mods
    TITLE = "Userbot Configuration for {}"
    TITLE = TITLE.format(phone)
    d.set_background_title(TITLE)
    while main_config(init):
        pass
    return db


def api_config():
    code, string = d.inputbox("Enter your API Hash")
    if code == d.OK:
        string1 = 'HASH = "' + string + '"'
        code, string = d.inputbox("Enter your API ID")
        string2 = 'ID = "' + string + '"'
        with open(os.path.join(utils.get_base_dir(), "api_token.py"), "w") as f:
            f.write(string1 + "\n" + string2 + "\n")
        d.msgbox("API Token and ID set.")


def logging_config():
    global db
    code, tag = d.menu(TITLE, choices=[("50", "CRITICAL"), ("40", "ERROR"),
                                       ("30", "WARNING"), ("20", "INFO"),
                                       ("10", "DEBUG"), ("0", "ALL")])
    if code == d.OK:
        db.setdefault(main.__name__, {})["loglevel"] = int(tag)


def factory_reset_check():
    global db
    code, tag = d.yesno("Do you REALLY want to erase ALL userbot data stored in Telegram cloud?\n"
                        + "Your existing Telegram chats will not be affected.")
    db = None


def main_config(init):
    if init:
        return api_config()
    choices = [("API Token and ID", "Configure API Token and ID"),
               ("Modules", "Modular configuration"),
               ("Logging", "Configure debug output")]
    if db.get("friendly-telegram.modules.loader", {}).get("loaded_modules", []) == []:
        choices += [("Enable lite mode", "Removes all non-core modules")]
    else:
        choices += [("Disable lite mode", "Enable all available modules")]
    choices += [("Factory reset", "Removes all userbot data stored in Telegram cloud")]
    code, tag = d.menu(TITLE, choices=choices)
    if code == d.OK:
        if tag == "Modules":
            modules_config()
        if tag == "API Token and ID":
            api_config()
        if tag == "Logging":
            logging_config()
        if tag == "Enable lite mode":
            db.setdefault("friendly-telegram.modules.loader", {})["loaded_modules"] = None
        if tag == "Disable lite mode":
            db.setdefault("friendly-telegram.modules.loader", {})["loaded_modules"] = []
        if tag == "Factory reset":
            factory_reset_check()
            return False
    else:
        return False
    return True
