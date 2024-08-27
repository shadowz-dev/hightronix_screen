import json
import logging

from typing import Union, Dict
from enum import Enum

from src.util.utils import camel_to_snake


class LangManager:

    LANG_FILE = "lang/{}.json"
    FALLBACK_LANG = "en"

    def __init__(self, lang: str = "en"):
        self._map = {}
        self._lang = lang.lower()
        self.load()

    def set_lang(self, lang: str):
        self._map = {}
        self._lang = lang.lower()
        self.load()

    def load(self, directory: str = "", prefix: str = ""):
        file_name = "{}{}{}".format(directory, "/" if directory else "", self.LANG_FILE.format(self._lang))
        fallback_file_name = "{}{}{}".format(directory, "/" if directory else "", self.LANG_FILE.format(self.FALLBACK_LANG))

        try:
            with open(file_name, 'r', encoding='utf-8') as file:
                for key, value in json.load(file).items():
                    self._map["{}{}{}".format(prefix, "_" if prefix else "", key)] = value
        except FileNotFoundError:
            logging.error(f"Lang file {file_name} not found, falling back to {fallback_file_name}")
            self._load_fallback(fallback_file_name, directory, prefix)

    def _load_fallback(self, fallback_file_name: str, directory: str = "", prefix: str = ""):
        # Load fallback language (e.g., English)
        try:
            with open(fallback_file_name, 'r', encoding='utf-8') as file:
                for key, value in json.load(file).items():
                    if key not in self._map:  # Only add if not already in map
                        self._map["{}{}{}".format(prefix, "_" if prefix else "", key)] = value
        except FileNotFoundError:
            logging.error(f"Fallback lang file {fallback_file_name} not found. Check your language files.")


    def map(self) -> dict:
        return self._map

    def get_lang(self, local_with_country: bool = False) -> str:
        return "{}_{}".format(self._lang, self._lang.upper()) if local_with_country else self._lang

    @staticmethod
    def enum_to_translation_key(enum: Enum) -> str:
        translation_key = str(enum)

        [classname, case] = translation_key.split('.')
        return "enum_{}_{}".format(
            camel_to_snake(classname),
            case.lower()
        )

    def translate(self, token) -> Union[Dict, str]:
        translation_key = str(token)

        if isinstance(token, type) and 'enum' in type(token).__name__.lower():
            values = {}
            for enum_item in token:
                tkey = self.enum_to_translation_key(enum_item)
                values[enum_item.value] = self.translate(tkey)
            return values
        elif isinstance(token, Enum):
            translation_key = self.enum_to_translation_key(token)

        map = self.map()

        translation = map[translation_key] if translation_key in map else translation_key

        return translation
