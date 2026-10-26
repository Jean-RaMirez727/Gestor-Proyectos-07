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

def map_result(result: Result[T, E], fn: Callable[[T], U]) -> Result[U, E]:
    match result:
        case Ok(value):
            return Ok(fn(value))
        case Err():
            return result

def bind(result: Result[T, E], fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
    match result:
        case Ok(value):
            return fn(value)
        case Err():
            return result