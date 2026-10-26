from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    value: T


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    error: E


Result = Union[Ok[T], Err[E]]


def map_ok(result: Result, fn: Callable[[T], U]) -> Result:
    """Aplica `fn` al valor de un Ok; un Err pasa sin cambios."""
    match result:
        case Ok(value):
            return Ok(fn(value))
        case Err():
            return result


# Nombre anterior, conservado por compatibilidad.
map_result = map_ok


def bind(result: Result, fn: Callable[[T], Result]) -> Result:
    """Encadena casos de uso que pueden fallar (si hay Err, no se ejecuta `fn`)."""
    match result:
        case Ok(value):
            return fn(value)
        case Err():
            return result
