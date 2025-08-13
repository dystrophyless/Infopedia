from locales.ru import RU
from locales.kz import KZ

def get_translations() -> dict[str, str | dict[str, str]]:
    return {
        "default": "ru",
        "kz": KZ,
        "ru": RU,
    }
