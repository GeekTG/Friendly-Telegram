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

# flake8: noqa: T001

"""Configuration menu, providing interface for users to control internals"""

import locale
import os
import inspect
import ast
import sys
import string

from dialog import Dialog, ExecutableNotFound

from . import utils, main


def _safe_input(*args, **kwargs):
    """Try to invoke input(*), print an error message if an EOFError or OSError occurs)"""
    try:
        return input(*args, **kwargs)
    except (EOFError, OSError):
        print()
        print("=" * 30)
        print()
        print("Hello. If you are seeing this, it means YOU ARE DOING SOMETHING WRONG!")
        print()
        print("It is likely that you tried to deploy to heroku - you cannot do this via the web interface.")
        print("To deploy to heroku, go to https://friendly-telegram.gitlab.io/heroku to learn more")
        print()
        print("If you're not using heroku, then you are using a non-interactive prompt but "
              "you have not got a session configured, meaning authentication to Telegram is impossible.")
        print()
        print("THIS ERROR IS YOUR FAULT. DO NOT REPORT IT AS A BUG!")
        print("Goodbye.")
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        return None


class TDialog():
    """Reimplementation of dialog.Dialog without external dependencies"""

    OK = True
    NOT_OK = False

    def __init__(self):
        self._title = ""

    # Similar interface to pythondialog
    def menu(self, title, choices):
        """Print a menu and get a choice"""

        print(self._title)
        print()
        print()
        print(title)
        print()
        biggest = max([len(k) for k, d in choices])
        i = 1
        for k, v in choices:
            print(" " + str(i) + ". " + k + (" " * (biggest + 2 - len(k))) + (v.replace("\n", "...\n      ")))
            i += 1
        while True:
            inp = _safe_input("Please enter your selection as a number, or 0 to cancel: ")
            if inp is None:
                inp = 0
            try:
                inp = int(inp)
                if inp == 0:
                    return (self.NOT_OK, "Cancelled")
                return (self.OK, choices[inp - 1][0])
            except (ValueError, IndexError):
                pass

    def inputbox(self, query):
        """Get a text input of the query"""

        print(self._title)
        print()
        print()
        print(query)
        print()
        inp = _safe_input("Please enter your response, or type nothing to cancel: ")
        if inp == "" or inp is None:
            return (self.NOT_OK, "Cancelled")
        return (self.OK, inp)

    def msgbox(self, msg):
        """Print some info"""

        print(self._title)
        print()
        print()
        print(msg)
        return self.OK

    def set_background_title(self, title):
        """Set the internal variable"""
        self._title = title

    def yesno(self, question):
        """Ask yes or no, default to no"""
        print(self._title)
        print()
        return self.OK if (_safe_input(question + " (y/N): ") or "").lower() == "y" else self.NOT_OK


TITLE = ""

if sys.stdout.isatty():
    try:
        DIALOG = Dialog(dialog="dialog", autowidgetsize=True)
        locale.setlocale(locale.LC_ALL, "")
    except (ExecutableNotFound, locale.Error):
        # Fall back to a terminal based configurator.
        DIALOG = TDialog()
else:
    DIALOG = TDialog()


MODULES = None
DB = None  # eww... meh.


# pylint: disable=W0603

def validate_value(value):
    """Convert string to literal or return string"""
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def modules_config():
    """Show menu of all modules and allow user to enter one"""
    global DB
    code, tag = DIALOG.menu("Modules", choices=[(module.name, inspect.cleandoc(getattr(module, "__doc__", None) or ""))
                                                for module in MODULES.modules if getattr(module, "config", {})])
    if code == DIALOG.OK:
        for mod in MODULES.modules:
            if mod.name == tag:
                # Match
                while not module_config(mod):
                    pass
        return modules_config()
    return None


def module_config(mod):
    """Show menu for specific module and allow user to set config items"""
    choices = []
    for key in getattr(mod, "config", {}).keys():
        if key.upper() == key:  # Constants only
            choices += [(key, getattr(mod.config, "getdoc", lambda k: "Undocumented key")(key))]
    code, tag = DIALOG.menu("Module configuration for {}".format(mod.name), choices=choices)
    if code == DIALOG.OK:
        code, value = DIALOG.inputbox(tag)
        if code == DIALOG.OK:
            DB.setdefault(mod.__module__, {}).setdefault("__config__",
                                                         {})[tag] = validate_value(value)
            DIALOG.msgbox("Config value set successfully")
        return False
    return True


def run(database, phone, init, mods):
    """Launch configurator"""
    global DB, MODULES, TITLE
    DB = database
    MODULES = mods
    TITLE = "Userbot Configuration for {}"
    TITLE = TITLE.format(phone)
    DIALOG.set_background_title(TITLE)
    while main_config(init):
        pass
    return DB


def api_config():
    """Request API config from user and set"""
    code, hash_value = DIALOG.inputbox("Enter your API Hash")
    if code == DIALOG.OK:
        if len(hash_value) != 32 or any(it not in string.hexdigits for it in hash_value):
            DIALOG.msgbox("Invalid hash")
            return
        string1 = "HASH = \"" + hash_value + "\""
        code, id_value = DIALOG.inputbox("Enter your API ID")
        if not id_value or any(it not in string.digits for it in id_value):
            DIALOG.msgbox("Invalid ID")
            return
        string2 = "ID = \"" + id_value + "\""
        with open(os.path.join(utils.get_base_dir(), "api_token.py"), "w") as file:
            file.write(string1 + "\n" + string2 + "\n")
        DIALOG.msgbox("API Token and ID set.")


def logging_config():
    """Ask the user to choose a loglevel and save it"""
    global DB
    code, tag = DIALOG.menu("Log Level", choices=[("50", "CRITICAL"), ("40", "ERROR"),
                                                  ("30", "WARNING"), ("20", "INFO"),
                                                  ("10", "DEBUG"), ("0", "ALL")])
    if code == DIALOG.OK:
        DB.setdefault(main.__name__, {})["loglevel"] = int(tag)


def factory_reset_check():
    """Make sure the user wants to factory reset"""
    global DB
    if DIALOG.yesno("Do you REALLY want to erase ALL userbot data stored in Telegram cloud?\n"
                    "Your existing Telegram chats will not be affected.") == DIALOG.OK:
        DB = None


def main_config(init):
    """Main menu"""
    if init:
        return api_config()
    choices = [("API Token and ID", "Configure API Token and ID"),
               ("Modules", "Modular configuration"),
               ("Logging", "Configure debug output"),
               ("Factory reset", "Removes all userbot data stored in Telegram cloud")]
    code, tag = DIALOG.menu("Main Menu", choices=choices)
    if code == DIALOG.OK:
        if tag == "Modules":
            modules_config()
        if tag == "API Token and ID":
            api_config()
        if tag == "Logging":
            logging_config()
        if tag == "Factory reset":
            factory_reset_check()
            return False
    else:
        return False
    return True
