# -*- coding: future_fstrings -*-

import locale, time, os, inspect

from dialog import Dialog

from . import loader, utils, main

TITLE = "Userbot Configuration"

d = Dialog(dialog="dialog")
locale.setlocale(locale.LC_ALL, '')

modules = loader.Modules.get()
modules.register_all([])

global db

def validate_value(string):
    try:
        return ast.literal_eval(string)
    except:
        return string

def modules_config():
    global db
    code, tag = d.menu(TITLE, choices=[(module.name, inspect.cleandoc(module.__doc__)) if len(module.config) > 0 else () for module in modules.modules])
    if code == d.OK:
        for mod in modules.modules:
            if mod.name == tag and len(mod.config) > 0:
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
    print(db)
    return db

def api_config():
    code, string = d.inputbox("Enter your API Token")
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
