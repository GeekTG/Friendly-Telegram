#    Friendly Telegram Userbot
#    by GeekTG Team

class Strings:
    def __init__(self, prefix, strings, babel):
        self._prefix = prefix
        self._strings = strings
        self._babel = babel

    def __getitem__(self, key):
        return self._babel.getkey(self._prefix + key) or self._strings[key]

    def __call__(self, key, message=None):
        if isinstance(message, str):
            lang_code = message
        elif message is None:
            lang_code = None
        else:
            lang_code = getattr(getattr(message, "sender", None), "lang_code", None)
        return self._babel.getkey(self._prefix + "." + key, lang_code) or self._strings[key]

    def __iter__(self):
        return self._strings.__iter__()
