from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True, slots=True)
class DomainError:
    message: str


@dataclass(frozen=True, slots=True)
class ValidationError(DomainError):
    pass


@dataclass(frozen=True, slots=True)
class TransitionError(DomainError):
    pass


@dataclass(frozen=True, slots=True)
class NotFoundError(DomainError):
    pass


# Errores que espera la interfaz y el servicio.


@dataclass(frozen=True, slots=True)
class InvalidTransition:
    origin: object
    target: object


@dataclass(frozen=True, slots=True)
class NotFound:
    entity: str
    entity_id: int | None = None


@dataclass(frozen=True, slots=True)
class PersistenceFailure:
    detail: str


AppError: TypeAlias = (
    ValidationError
    | TransitionError
    | NotFoundError
    | InvalidTransition
    | NotFound
    | PersistenceFailure
)
