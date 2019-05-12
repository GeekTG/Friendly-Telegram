#Userbot configuration

import locale
import time

from dialog import Dialog

import loader

d = Dialog(dialog="dialog")
locale.setlocale(locale.LC_ALL, '')


while True:
    code, tag = d.menu("Userbot configuration",
                       choices=[("API Token and ID", "Configure API Token and ID")])

    if code == d.OK:
        #if tag == "Modules":
            #d.infobox("Updating modules list...")
            #time.sleep(1)
            #Modules = loader.Modules.get()
            #Modules.register_all()
            #code, tag = d.menu("Userbot configuration",
            #                   choices=[Modules.modules])

        if tag == "API Token and ID":
            code, string = d.inputbox("Enter your API Token")
            if code == d.OK:
                f = open("api_token.py", "w")
                string1 = 'HASH="' + string + '"'
                code, string = d.inputbox("Enter your API ID")
                string2 = 'ID="' + string + '"'
                f.write(string1 + "\n" + string2)
                f.close()
                d.msgbox("API Token and ID set.")
    else:
        timer = 3
        for i in range(timer):
            d.infobox("Program will exit in " + str(timer) + "...")
            time.sleep(1)
            timer -= 1
        exit()
