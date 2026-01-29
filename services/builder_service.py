from abc import ABC, abstractmethod
import numpy as np

from database.models import Term, Source, Definition


class ITermBuilder(ABC):
    @abstractmethod
    def reset(self) -> "ITermBuilder":
        pass

    @abstractmethod
    def set_term_name(self, *, name: str) -> "ITermBuilder":
        pass

    @abstractmethod
    def add_source(self, *, source_name: str) -> "ITermBuilder":
        pass

    @abstractmethod
    def add_definition(
        self, *, text: str, topic: str | None = None, page: int | None = None
    ) -> "ITermBuilder":
        pass

    @abstractmethod
    def set_embedding_generator(self, embedder) -> "ITermBuilder":
        pass

    @abstractmethod
    def build(self) -> Term:
        pass


class TermBuilder(ITermBuilder):
    def __init__(self):
        self.embedder = None
        self.reset()

    def reset(self) -> "TermBuilder":
        self.term: Term = Term(name="")
        self.term.sources = []
        self.current_source: Source | None = None
        return self

    def set_term_name(self, *, name: str) -> "TermBuilder":
        if not name or not name.strip():
            raise ValueError("Имя термина не может быть пустым.")

        self.term.name = name.strip()
        return self

    def add_source(self, *, source_name: str) -> "TermBuilder":
        if not source_name or not source_name.strip():
            raise ValueError("Имя источника не может быть пустым.")

        source = Source(name=source_name.strip())
        source.term = self.term
        source.definitions = []

        self.term.sources.append(source)
        self.current_source = source

        return self

    def add_definition(
        self, *, text: str, topic: str | None = None, page: int | None = None
    ) -> "TermBuilder":
        if self.current_source is None:
            raise ValueError(
                "Перед добавлением определения необходимо добавить источник."
            )

        if not text or not text.strip():
            raise ValueError("Текст определения не может быть пустым.")

        definition = Definition(
            text=text.strip(),
            topic=topic.strip() if topic else None,
            page=page,
            source=self.current_source,
        )

        if self.embedder is not None:
            embedding = self.embedder.encode(
                definition.text, convert_to_numpy=True, normalize_embeddings=True
            )
            definition.embedding = np.asarray(embedding).ravel().tolist()

        self.current_source.definitions.append(definition)
        return self

    def set_embedding_generator(self, embedder) -> "TermBuilder":
        self.embedder = embedder
        return self

    def build(self) -> Term:
        if not self.term.name:
            raise ValueError("Название термина обязательно для указания.")

        if not self.term.sources:
            raise ValueError("Термин должен содержать хотя бы один источник.")

        for source in self.term.sources:
            if not source.definitions:
                raise ValueError(
                    f"Источник '{source.name}' не содержит ни одного определения."
                )

        term = self.term
        self.reset()
        return term
