# -*- coding: future_fstrings -*-

import locale, time, os, inspect, ast

from dialog import Dialog, ExecutableNotFound

from . import loader, utils, main

class TDialog():
    OK=0
    NOT_OK=1
    # Similar interface to pythondialog
    def menu(self, title, choices):
        print()
        print()
        print(title)
        print()
        biggest = max([len(k) for k,d in choices])
        i = 1
        for k, d in choices:
            print(" "+str(i)+". "+k+(" "*(biggest+2-len(k)))+(d.replace("\n", "...\n      ")))
            i += 1
        while True:
            inp = input("Please enter your selection as a number, or 0 to cancel: ")
            try:
                inp = int(inp)
                if inp == 0:
                    return (self.NOT_OK, "Cancelled")
                return (self.OK, choices[inp-1][0])
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

TITLE = "Userbot Configuration"

try:
    d = Dialog(dialog="dialog")
except ExecutableNotFound:
    # Fall back to a terminal based configurator.
    d = TDialog()

locale.setlocale(locale.LC_ALL, '')

modules = loader.Modules()
modules.register_all([])

global db

def validate_value(string):
    try:
        return ast.literal_eval(string)
    except:
        return string

def modules_config():
    global db
    code, tag = d.menu(TITLE, choices=[(module.name, inspect.cleandoc(module.__doc__)) for module in modules.modules])
    if code == d.OK:
        for mod in modules.modules:
            if mod.name == tag:
                # Match
                choices = [("Enabled", "Set to 0 to disable this module, 1 to enable")]
                for key, value in mod.config.items():
                    if key.upper() == key: # Constants only
                        choices += [(key, "")]
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
                                db.setdefault(main.__name__, {}).setdefault("disable_modules", []).remove(mod.__module__)
                            except ValueError:
                                pass
                            if not enabled:
                                db.setdefault(main.__name__, {}).setdefault("disable_modules", []).append(mod.__module__)
                        else:
                            db.setdefault(mod.__module__, {}).setdefault("__config__", {})[tag] = validate_value(string)
                modules_config()
                return
    else:
        return

def run(database, init):
    global db
    db = database
    while main_config(init):
        pass
    return db

def api_config():
    code, string = d.inputbox("Enter your API Hash")
    if code == d.OK:
        string1 = 'HASH="' + string + '"'
        code, string = d.inputbox("Enter your API ID")
        string2 = 'ID="' + string + '"'
        f = open(os.path.join(utils.get_base_dir(), "api_token.py"), "w")
        f.write(string1 + "\n" + string2)
        f.close()
        d.msgbox("API Token and ID set.")

def logging_config():
    global db
    code, tag = d.menu(TITLE, choices=[("50", "CRITICAL"), ("40", "ERROR"), ("30", "WARNING"), ("20", "INFO"), ("10", "DEBUG"), ("0", "ALL")])
    if code == d.OK:
        db.setdefault(main.__name__, {})["loglevel"] = int(tag)

def main_config(init):
    code, tag = d.menu(TITLE, choices=[("API Token and ID", "Configure API Token and ID"), ("Modules", "Modules"), ("Logging", "Configure debug output")])
    if code == d.OK:
        if tag == "Modules":
            modules_config()
        if tag == "API Token and ID":
            api_config()
        if tag == "Logging":
            logging_config()
    else:
        return False
    return True
