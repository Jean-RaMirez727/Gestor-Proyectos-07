"""Decorador transversal: registra operaciones y mide su duración.

No contiene reglas de dominio; sólo observa la llamada (preocupación externa).
"""
import functools
import logging
import time
from typing import Callable

log = logging.getLogger("gestor")


def logged(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            ms = (time.perf_counter() - start) * 1000
            log.info("%s terminó en %.2f ms", func.__name__, ms)

    return wrapper
