import json
import os
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

INCOMING_PATH = os.path.join(BASE_DIR, "database", "incoming_terms.json")
TARGET_PATH = os.path.join(BASE_DIR, "database", "terms.json")


def load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read().strip()
        if not raw:
            return {}
        return json.loads(raw) or {}


def save_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def normalise_definition(text: str) -> str:
    return str(text).strip().lower()


def capitalise_first_letter(text: str) -> str:
    if not isinstance(text, str):
        return text

    text = text.strip()
    if not text:
        return text

    return text[0].upper() + text[1:]


def normalise_incoming_data(data: dict) -> dict:
    """
    - Делает первую букву term_name заглавной
    - Делает первую букву definition заглавной
    """
    normalised = {}

    for term, sources in data.items():
        if not isinstance(term, str):
            continue

        new_term = capitalise_first_letter(term)

        if not isinstance(sources, dict):
            continue

        normalised_sources = {}

        for source, items in sources.items():
            if not isinstance(items, list):
                continue

            new_items = []
            for item in items:
                if not isinstance(item, dict):
                    continue

                item = item.copy()

                if "definition" in item:
                    item["definition"] = capitalise_first_letter(item["definition"])

                new_items.append(item)

            normalised_sources[source] = new_items

        normalised[new_term] = normalised_sources

    return normalised


def merge_terms(target: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    """
    Формат:
    {
      "Term": {
         "Source A": [ {definition, topic, page}, ... ],
         "Source B": [ ... ]
      },
      ...
    }

    Правило дедупа:
    В рамках одного term+source, если definition совпадает без учёта регистра — НЕ добавляем.
    """
    if not isinstance(target, dict):
        raise ValueError("terms.json должен быть JSON-объектом (dict) на верхнем уровне.")
    if not isinstance(incoming, dict):
        raise ValueError("incoming_terms.json должен быть JSON-объектом (dict) на верхнем уровне.")

    for term, sources in incoming.items():
        if not isinstance(term, str) or not term.strip():
            continue
        term = term.strip()

        if not isinstance(sources, dict):
            continue

        # если термина нет — добавляем целиком (как есть)
        if term not in target or not isinstance(target.get(term), dict):
            target[term] = sources
            continue

        # термин есть → идём по источникам
        for source, items in sources.items():
            if not isinstance(source, str) or not source.strip():
                continue
            source = source.strip()

            if not isinstance(items, list):
                continue

            # если источника нет — добавляем целиком
            if source not in target[term] or not isinstance(target[term].get(source), list):
                target[term][source] = items
                continue

            existing_items = target[term][source]

            # собираем все уже существующие definitions (case-insensitive)
            existing_definitions = {
                normalise_definition(x.get("definition", ""))
                for x in existing_items
                if isinstance(x, dict) and x.get("definition")
            }

            # добавляем только те, у которых definition ещё не встречалась в этом source
            for item in items:
                if not isinstance(item, dict):
                    continue

                raw_def = item.get("definition", "")
                if not raw_def:
                    continue

                def_key = normalise_definition(raw_def)
                if not def_key:
                    continue

                if def_key in existing_definitions:
                    continue

                existing_items.append(item)
                existing_definitions.add(def_key)

    return target


def main() -> None:
    incoming = load_json(INCOMING_PATH)
    if not incoming:
        print("Входной файл пуст — делать нечего")
        return

    incoming = normalise_incoming_data(incoming)

    target = load_json(TARGET_PATH)

    merged = merge_terms(target, incoming)

    save_json(TARGET_PATH, merged)

    # очищаем входной файл только после успешной записи terms.json
    save_json(INCOMING_PATH, {})

    print("✔ Данные объединены, входной файл очищен")


if __name__ == "__main__":
    main()