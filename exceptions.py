class TermAppError(Exception):
    pass


class TermNotFoundByNameError(TermAppError):
    def __init__(self, term_name: str):
        self.term_name = term_name
        super().__init__(f"Термин `name`='{term_name}' не найден.")


class TermNotFoundByIdError(TermAppError):
    def __init__(self, term_id: int):
        self.term_id = term_id
        super().__init__(f"Термин `id`='{term_id}' не найден.")


class TermPresentationError(TermAppError):
    pass


class NoSourcesFoundError(TermAppError):
    pass


class SecurityPayloadError(TermAppError):
    pass

