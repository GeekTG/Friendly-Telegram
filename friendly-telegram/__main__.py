#    Friendly Telegram Userbot
#    by GeekTG Team

# flake8: noqa: T001

"""Initial entrypoint"""

import sys
if sys.version_info < (3, 6, 0):
    print("Error: you must use at least Python version 3.6.0")  # pragma: no cover
else:
    if sys.version_info >= (3, 9, 0):
        print("Warning: you are using an untested Python version")  # pragma: no cover
    if __package__ != "friendly-telegram":  # In case they did python __main__.py
        print("Error: you cannot run this as a script; you must execute as a package")  # pragma: no cover
    else:
        from . import log
        log.init()
        try:
            from . import main
        except ModuleNotFoundError:  # pragma: no cover
            print("Error: you have not installed all dependencies correctly.")
            print("Please install all dependencies from requirements.txt")
            raise
        else:
            if __name__ == '__main__':
                main.main()  # Execute main function
