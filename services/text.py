import re

def normalize(text: str) -> str:
    normalized: str = text.lower()
    kazakh_translit = {
        'ә': 'а', 'ғ': 'г', 'қ': 'к', 'ң': 'н',
        'ө': 'о', 'ұ': 'у', 'ү': 'у', 'һ': 'х',
        'і': 'и', 'Ә': 'а', 'Ғ': 'г', 'Қ': 'к',
        'Ң': 'н', 'Ө': 'о', 'Ұ': 'у', 'Ү': 'у',
        'Һ': 'х', 'І': 'и'
    }
    for char, replacement in kazakh_translit.items():
        normalized = normalized.replace(char, replacement)
    normalized = re.sub(r'[^a-zа-яё0-9\s]', '', normalized)
    return normalized
