from dataclasses import dataclass


@dataclass
class FeedbackStat:
    definition_id: int
    term_name: str
    total_queries: int
    correct_queries: int
    accuracy: int

    @property
    def short_term_name(self) -> str:
        max_len: int = 20

        if len(self.term_name) <= max_len:
            return self.term_name

        words: list[str] = self.term_name.split()
        result: list[str] = []
        length: int = 0

        for word in words:
            add_len: int = len(word) if not result else len(word) + 1

            if length + add_len <= max_len:
                result.append(word)
                length += add_len
            else:
                break

        return " ".join(result) + "..."
