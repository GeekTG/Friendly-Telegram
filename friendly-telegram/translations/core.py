import logging, os, json

from .. import utils

logger = logging.getLogger(__name__)

from babel import Locale, negotiate_locale

class Translator:
    def __init__(self, languages=["en"]):
        path = os.path.join(os.path.dirname(utils.get_base_dir()), "translations")
        try:
            files = filter(lambda x: len(x) > 5 and x[-5:] == ".json", os.listdir(path))
        except FileNotFoundError:
            logger.exception("Unable to list %s", path)
            files = []
        self._data = {}
        for translation_file in files:
            try:
                with open(os.path.join(path, translation_file), "r") as f:
                    self._data.update(**json.loads(f.read()))
            except json.decoder.JSONDecodeError:
                logger.exception("Unable to decode %s", os.path.join(path, translation_file))
        self._languages = languages
    def set_preferred_languages(self, languages):
        self._languages = languages
    def gettext(self, english_text):
        locales = []
        for locale, strings in self._data.items():
            if english_text in strings:
                locales += [locale]
        locale = negotiate_locale(self._languages, locales)
        return self._data.get(locale, {}).get(english_text, english_text)
