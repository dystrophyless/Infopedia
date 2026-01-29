from locales.kz import KZ
from locales.ru import RU


def get_translations() -> dict[str, str | dict[str, str]]:
    return {
        "default": "ru",
        "kz": KZ,
        "ru": RU,
    }
