from dataclasses import dataclass

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