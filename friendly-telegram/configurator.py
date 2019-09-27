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
import sys
import string

from dialog import Dialog, ExecutableNotFound

from . import utils, main


class TDialog():
    OK = 0
    NOT_OK = 1

    def _safe_input(self, *args, **kwargs):
        try:
            return input(*args, **kwargs)
        except (EOFError, OSError):
            print()
            print("=" * 30)
            print()
            print("Hello. If you are seeing this, it means YOU ARE DOING SOMETHING WRONG!")
            print()
            print("It is likely that you tried to deploy to heroku - you cannot do this via the web interface.")
            print("To deploy to heroku, go to https://friendly-telegram.github.io/heroku to learn more")
            print()
            print("If you're not using heroku, then you are using a non-interactive prompt but "
                  + "you have not got a session configured, meaning authentication to Telegram is impossible.")
            print()
            print("THIS ERROR IS YOUR FAULT. DO NOT REPORT IT AS A BUG!")
            print("Goodbye.")
            sys.exit(1)

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
            inp = self._safe_input("Please enter your selection as a number, or 0 to cancel: ")
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
        inp = self._safe_input("Please enter your response, or type nothing to cancel: ")
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
        return self._safe_input(question + "y/N").lower() == "y"


TITLE = ""

try:
    d = Dialog(dialog="dialog", autowidgetsize=True)
except ExecutableNotFound:
    # Fall back to a terminal based configurator.
    d = TDialog()

locale.setlocale(locale.LC_ALL, '')

global modules
global db  # eww... meh.


def validate_value(s):
    try:
        return ast.literal_eval(s)
    except Exception:
        return s


def modules_config():
    global db
    code, tag = d.menu("Modules", choices=[(module.name, inspect.cleandoc(getattr(module, "__doc__", None) or ""))
                                           for module in modules.modules])
    if code == d.OK:
        for mod in modules.modules:
            if mod.name == tag:
                # Match
                while True:
                    choices = [("Enabled", "Set to 0 to disable this module, 1 to enable")]
                    for key, value in getattr(mod, "config", {}).items():
                        if key.upper() == key:  # Constants only
                            choices += [(key, getattr(mod.config, "getdoc", lambda k: "Undocumented key")(key))]
                    code, tag = d.menu("Module configuration for {}".format(mod.name), choices=choices)
                    if code == d.OK:
                        code, s = d.inputbox(tag)
                        if code == d.OK:
                            if tag == "Enabled":
                                try:
                                    enabled = int(s) > 0
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
                                                                             {})[tag] = validate_value(s)
                    else:
                        break
                return modules_config()
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
    code, hash = d.inputbox("Enter your API Hash")
    if code == d.OK:
        if len(hash) != 32 or not all(it in string.hexdigits for it in hash):
            d.msgbox("Invalid hash")
            return
        string1 = 'HASH = "' + hash + '"'
        code, id = d.inputbox("Enter your API ID")
        if len(id) == 0 or not all(it in string.digits for it in id):
            d.msgbox("Invalid ID")
            return
        string2 = 'ID = "' + id + '"'
        with open(os.path.join(utils.get_base_dir(), "api_token.py"), "w") as f:
            f.write(string1 + "\n" + string2 + "\n")
        d.msgbox("API Token and ID set.")


def logging_config():
    global db
    code, tag = d.menu("Log Level", choices=[("50", "CRITICAL"), ("40", "ERROR"),
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
    code, tag = d.menu("Main Menu", choices=choices)
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
