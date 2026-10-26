"""Conversión de errores del núcleo en mensajes comprensibles (shell)."""
from app.domain.errors import AppError, InvalidTransition, NotFound, PersistenceFailure, ValidationError


def to_message(error: AppError) -> str:
    match error:
        case ValidationError(_, message):
            return message
        case InvalidTransition(origin, target):
            return f"No se puede mover una tarea de «{origin.value}» a «{target.value}»."
        case NotFound(entity, _):
            return f"No se encontró el {entity} indicado."
        case PersistenceFailure(detail):
            return f"Problema al guardar o leer los datos: {detail}"
        case _:
            return "Ocurrió un error inesperado."
