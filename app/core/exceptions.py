# app/app/core/exceptions.py
#--------------------------------------------

class DomainError(Exception):
    """Базовое исключение бизнес-логики."""


class ThreadNotFoundError(DomainError):
    """Тред не найден."""


class ThreadAccessDeniedError(DomainError):
    """Пользователь не владеет тредом."""


class ActionNotFoundError(DomainError):
    """Pending action не найден."""


class ActionAlreadyResolvedError(DomainError):
    """Действие уже одобрено или отклонено."""