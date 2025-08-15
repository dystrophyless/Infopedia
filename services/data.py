import json

from services.text import normalize


def load_terms(path: str = "database/terms.json") -> dict:
    with open(path, encoding="utf-8") as f:
        terms = json.load(f)
    return terms


def load_indexed_terms(path: str = "database/terms.json") -> list[dict[str, str]]:
    with open(path, encoding="utf-8") as f:
        terms = json.load(f)

    indexed_terms = []
    for term, sources in terms.items():
        term_entry = {
            "term": term,
            "normalized": normalize(term),
            "sources": sources
        }
        indexed_terms.append(term_entry)

    return indexed_terms


def generate_id_maps(terms: dict) -> tuple[dict[int, str], dict[str, int], dict[int, str], dict[str, int]]:
    term_ids = {}
    term_names_to_ids = {}
    source_ids = {}
    source_names_to_ids = {}

    term_id_counter = 1
    source_id_counter = 1

    for term_name, sources in terms.items():
        term_ids[term_id_counter] = term_name
        term_names_to_ids[term_name] = term_id_counter
        term_id_counter += 1

        for source_name in sources:
            if source_name not in source_names_to_ids:
                source_ids[source_id_counter] = source_name
                source_names_to_ids[source_name] = source_id_counter
                source_id_counter += 1

    return term_ids, term_names_to_ids, source_ids, source_names_to_ids