from dataclasses import replace
from typing import Callable, Sequence

from app.core.result import Err, Ok, Result
from app.domain.errors import TransitionError, ValidationError
from app.domain.models import EstadoKanban, Prioridad, Tarea

MAX_TITULO = 100


def validar_transicion_kanban(origen: EstadoKanban, destino: EstadoKanban) -> bool:
    """Pattern matching para validar transiciones del tablero Kanban."""
    match (origen, destino):
        case (o, d) if o == d:
            return True
        case (EstadoKanban.PENDIENTE, EstadoKanban.EN_PROGRESO):
            return True
        case (EstadoKanban.EN_PROGRESO, EstadoKanban.EN_REVISION):
            return True
        case (EstadoKanban.EN_PROGRESO, EstadoKanban.PENDIENTE):
            return True
        case (EstadoKanban.EN_REVISION, EstadoKanban.TERMINADA):
            return True
        case (EstadoKanban.EN_REVISION, EstadoKanban.EN_PROGRESO):
            return True
        case _:
            return False


def mover_tarea(tarea: Tarea, nuevo_estado: EstadoKanban) -> Result[Tarea, TransitionError]:
    """Retorna una nueva Tarea inmutable o un Err si la transición no es válida."""
    if not validar_transicion_kanban(tarea.estado, nuevo_estado):
        return Err(TransitionError(f"No se permite pasar de '{tarea.estado.value}' a '{nuevo_estado.value}'."))
    return Ok(replace(tarea, estado=nuevo_estado))


def crear_tarea(
    id: str,
    nodo_wbs_id: str,
    titulo: str,
    descripcion: str = "",
    prioridad: Prioridad = Prioridad.MEDIA,
    responsable_id: str | None = None,
) -> Result[Tarea, ValidationError]:
    """Crea una tarea inmutable validando las restricciones de entrada."""
    t_clean = (titulo or "").strip()
    if not t_clean:
        return Err(ValidationError("El título de la tarea no puede estar vacío."))
    if len(t_clean) > MAX_TITULO:
        return Err(ValidationError(f"El título supera el límite de {MAX_TITULO} caracteres."))

    return Ok(
        Tarea(
            id=id,
            nodo_wbs_id=nodo_wbs_id,
            titulo=t_clean,
            descripcion=descripcion.strip(),
            prioridad=prioridad,
            estado=EstadoKanban.PENDIENTE,
            responsable_id=responsable_id.strip() if responsable_id else None,
        )
    )


# Closures y funciones de orden superior para filtrado funcional
def filtrar_por_estado(estado: EstadoKanban | None) -> Callable[[Tarea], bool]:
    return lambda tarea: True if estado is None else tarea.estado == estado


def filtrar_por_responsable(responsable_id: str | None) -> Callable[[Tarea], bool]:
    return lambda tarea: True if responsable_id is None else tarea.responsable_id == responsable_id


def aplicar_filtro(tareas: Sequence[Tarea], criterio: Callable[[Tarea], bool]) -> tuple[Tarea, ...]:
    return tuple(t for t in tareas if criterio(t))