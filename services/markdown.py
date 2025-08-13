import re

def fix_special_symbols(text: str) -> str:
    special_chars = r'.!\[\]{}()|=+-#'
    return re.sub(f'([{re.escape(special_chars)}])', r'\\\1', text)
