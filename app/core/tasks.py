"""Núcleo funcional de tareas/Kanban: funciones puras, sin I/O."""
from dataclasses import replace
from typing import Callable, Mapping, Sequence

from app.core.result import Err, Ok, Result
from app.domain.errors import InvalidTransition, NotFound, TransitionError, ValidationError
from app.domain.models import Member, Priority, Status, Task, Tarea, WorkPackage

MAX_TITULO = 100

# Del «cómo» al «qué»: las reglas del tablero se declaran como datos.
ALLOWED_TRANSITIONS: Mapping[Status, tuple[Status, ...]] = {
    Status.PENDING: (Status.IN_PROGRESS,),
    Status.IN_PROGRESS: (Status.IN_REVIEW, Status.PENDING),
    Status.IN_REVIEW: (Status.DONE, Status.IN_PROGRESS),
    Status.DONE: (Status.IN_PROGRESS,),
}

_PRIORITY_RANK = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}

Predicate = Callable[[Task], bool]


def allowed_transitions(status: Status) -> tuple[Status, ...]:
    return ALLOWED_TRANSITIONS.get(status, ())


# ---------------------------------------------------------------------------
# Casos de uso puros (modelo usado por la aplicación)
# ---------------------------------------------------------------------------
def create_task(project_id: int, package_id: int, title: str, priority: Priority,
                assignee_id: int | None, packages: Sequence[WorkPackage],
                members: Sequence[Member]) -> Result:
    clean = (title or "").strip()
    if not clean:
        return Err(ValidationError("El título de la tarea no puede estar vacío."))
    if len(clean) > MAX_TITULO:
        return Err(ValidationError(f"El título supera el límite de {MAX_TITULO} caracteres."))
    if all(p.id != package_id for p in packages):
        return Err(NotFound("paquete", package_id))
    if assignee_id is not None and all(m.id != assignee_id for m in members):
        return Err(NotFound("integrante", assignee_id))
    return Ok(Task(None, project_id, package_id, clean, assignee_id, priority, Status.PENDING))


def change_status(task: Task, target: Status) -> Result:
    """Devuelve una tarea nueva o Err(InvalidTransition); la original no cambia."""
    match (task.status, target):
        case (origin, dest) if dest in allowed_transitions(origin):
            return Ok(replace(task, status=dest))
        case (origin, dest):
            return Err(InvalidTransition(origin, dest))


def assign(task: Task, member_id: int | None, members: Sequence[Member]) -> Result:
    if member_id is not None and all(m.id != member_id for m in members):
        return Err(NotFound("integrante", member_id))
    return Ok(replace(task, assignee_id=member_id))


# ---------------------------------------------------------------------------
# Consultas: closures y funciones de orden superior
# ---------------------------------------------------------------------------
def find_by_id(tasks: Sequence[Task], task_id: int) -> Task | None:
    """None significa «no existe» (distinto de una lista vacía)."""
    return next((t for t in tasks if t.id == task_id), None)


def by_status(status: Status | None) -> Predicate:
    return lambda t: status is None or t.status == status


def by_assignee(assignee_id: int | None) -> Predicate:
    return lambda t: assignee_id is None or t.assignee_id == assignee_id


def by_priority(priority: Priority | None) -> Predicate:
    return lambda t: priority is None or t.priority == priority


def all_of(*predicates: Predicate) -> Predicate:
    return lambda t: all(p(t) for p in predicates)


def build_filter(status: Status | None = None, assignee_id: int | None = None,
                 priority: Priority | None = None) -> Predicate:
    return all_of(by_status(status), by_assignee(assignee_id), by_priority(priority))


def select(tasks: Sequence[Task], predicate: Predicate) -> tuple[Task, ...]:
    return tuple(t for t in tasks if predicate(t))


def sort_tasks(tasks: Sequence[Task]) -> tuple[Task, ...]:
    """Mayor prioridad primero; a igualdad, por título y luego por id."""
    return tuple(sorted(tasks, key=lambda t: (_PRIORITY_RANK[t.priority], t.title.casefold(), t.id or 0)))


def board(tasks: Sequence[Task]) -> dict[Status, tuple[Task, ...]]:
    """Agrupa por columna del tablero (siempre incluye las 4 columnas)."""
    return {s: select(tasks, by_status(s)) for s in Status}


def pending_by_member(tasks: Sequence[Task], members: Sequence[Member]) -> dict[int, int]:
    """Tareas no terminadas por integrante (0 si no tiene)."""
    return {m.id: len(select(tasks, all_of(by_assignee(m.id), lambda t: t.status != Status.DONE)))
            for m in members}


# ---------------------------------------------------------------------------
# Modelo en español (Tarea / EstadoKanban), conservado por compatibilidad
# ---------------------------------------------------------------------------
def validar_transicion_kanban(origen: Status, destino: Status) -> bool:
    """Pattern matching para validar transiciones del tablero Kanban."""
    match (origen, destino):
        case (o, d) if d in allowed_transitions(o):
            return True
        case _:
            return False


def mover_tarea(tarea: Tarea, nuevo_estado: Status) -> Result[Tarea, TransitionError]:
    """Retorna una nueva Tarea inmutable o un Err si la transición no es válida."""
    if not validar_transicion_kanban(tarea.estado, nuevo_estado):
        return Err(TransitionError(f"No se permite pasar de '{tarea.estado.value}' a '{nuevo_estado.value}'."))
    return Ok(replace(tarea, estado=nuevo_estado))


def crear_tarea(
    id: str,
    nodo_wbs_id: str,
    titulo: str,
    descripcion: str = "",
    prioridad: Priority = Priority.MEDIUM,
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
            descripcion=(descripcion or "").strip(),
            prioridad=prioridad,
            estado=Status.PENDING,
            responsable_id=responsable_id.strip() if responsable_id else None,
        )
    )


def filtrar_por_estado(estado: Status | None) -> Callable[[Tarea], bool]:
    return lambda tarea: estado is None or tarea.estado == estado


def filtrar_por_responsable(responsable_id: str | None) -> Callable[[Tarea], bool]:
    return lambda tarea: responsable_id is None or tarea.responsable_id == responsable_id


def aplicar_filtro(tareas: Sequence[Tarea], criterio: Callable[[Tarea], bool]) -> tuple[Tarea, ...]:
    return tuple(t for t in tareas if criterio(t))
