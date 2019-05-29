#!/usr/bin/env python3.7

import locale, time, os

from dialog import Dialog

from . import loader, utils

try:
    from . import config
    new_config = False
except:
    new_config = True

TITLE = "Userbot Configuration"

d = Dialog(dialog="dialog")
locale.setlocale(locale.LC_ALL, '')

modules = loader.Modules.get()
modules.register_all()

def open_config(mode = "a"):
    return open(os.path.join(utils.get_base_dir(), "config.py"), mode)

def validate_value(string):
    try:
        ast.literal_eval(string)
        return string
    except:
        return '"'+ (string.replace('"', r'\"')) + '"'

def modules_config():
    code, tag = d.menu(TITLE, choices=[(module.name, module.help) if len(module.config) > 0 else () for module in modules.modules])
    if code == d.OK:
        for mod in modules.modules:
            if mod.name == tag and len(mod.config) > 0:
                # Match
                choices = []
                for key, value in mod.config.items():
                    if key.upper() == key: # Constants only
                        choices += [(key, "")]
                code, tag = d.menu(TITLE, choices=choices)
                if code == d.OK:
                    code, string = d.inputbox(tag)
                    if code == d.OK:
                        print(key+"="+string)
                        f = open_config()
                        f.write("\n"+key+"="+validate_value(string))
                        f.close()
                modules_config()
                return
    else:
        return

def main():
    if new_config:
        open_config("w").close()
    while main_config():
        pass

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

def main_config():
    code, tag = d.menu(TITLE, choices=[("API Token and ID", "Configure API Token and ID"), ("Modules", "Modules")])
    if code == d.OK:
        if tag == "Modules":
            modules_config()
        if tag == "API Token and ID":
            api_config()
    else:
        return False
    return True
