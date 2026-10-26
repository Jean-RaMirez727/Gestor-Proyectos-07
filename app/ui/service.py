"""Shell imperativa: coordina repositorio + funciones puras del core.

Patrón de cada caso de uso: leer datos -> función pura -> guardar -> Result.
"""
from typing import Callable

from app.adapters.instrumentation import logged
from app.core import tasks as T
from app.core import wbs as W
from app.core.result import Err, Ok, Result, bind
from app.domain.errors import NotFound, PersistenceFailure, ValidationError
from app.domain.models import Priority, Status
from app.ports.repository import PersistenceError, Repository


def _safe(operation: Callable[[], Result]) -> Result:
    """Los fallos de infraestructura se convierten en Err(PersistenceFailure)."""
    try:
        return operation()
    except PersistenceError as exc:
        return Err(PersistenceFailure(str(exc)))


def _required(value, entity: str, entity_id: int | None) -> Result:
    return Ok(value) if value is not None else Err(NotFound(entity, entity_id))


class AppService:
    def __init__(self, repo: Repository):
        self._repo = repo

    # --- proyectos ---
    @logged
    def create_project(self, name: str, description: str = "") -> Result:
        return _safe(lambda: bind(W.create_project(name, description),
                                  lambda p: Ok(self._repo.add_project(p))))

    @logged
    def list_projects(self) -> Result:
        return _safe(lambda: Ok(self._repo.list_projects()))

    @logged
    def get_project(self, project_id: int) -> Result:
        return _safe(lambda: _required(self._repo.get_project(project_id), "proyecto", project_id))

    # --- integrantes ---
    @logged
    def add_member(self, project_id: int, name: str) -> Result:
        return _safe(lambda: bind(
            W.create_member(project_id, name, self._repo.list_members(project_id)),
            lambda m: Ok(self._repo.add_member(m))))

    @logged
    def members(self, project_id: int) -> Result:
        return _safe(lambda: Ok(self._repo.list_members(project_id)))

    # --- EDT ---
    @logged
    def add_package(self, project_id: int, name: str, parent_id: int | None) -> Result:
        return _safe(lambda: bind(
            W.create_package(project_id, name, parent_id, self._repo.list_packages(project_id)),
            lambda p: Ok(self._repo.add_package(p))))

    @logged
    def packages(self, project_id: int) -> Result:
        return _safe(lambda: Ok(self._repo.list_packages(project_id)))

    # --- tareas ---
    @logged
    def add_task(self, project_id: int, package_id: int | None, title: str,
                 priority: Priority, assignee_id: int | None) -> Result:
        def op() -> Result:
            if package_id is None:
                return Err(ValidationError("Selecciona un paquete de la EDT para la tarea."))
            return bind(
                T.create_task(project_id, package_id, title, priority, assignee_id,
                              self._repo.list_packages(project_id), self._repo.list_members(project_id)),
                lambda t: Ok(self._repo.add_task(t)))
        return _safe(op)

    @logged
    def move_task(self, task_id: int, target: Status) -> Result:
        return _safe(lambda: bind(
            _required(self._repo.get_task(task_id), "tarea", task_id),
            lambda t: bind(T.change_status(t, target), lambda moved: Ok(self._repo.update_task(moved)))))

    @logged
    def assign_task(self, task_id: int, member_id: int | None) -> Result:
        def with_task(task):
            return bind(T.assign(task, member_id, self._repo.list_members(task.project_id)),
                        lambda updated: Ok(self._repo.update_task(updated)))
        return _safe(lambda: bind(_required(self._repo.get_task(task_id), "tarea", task_id), with_task))

    @logged
    def tasks(self, project_id: int, status: Status | None = None,
              assignee_id: int | None = None, priority: Priority | None = None) -> Result:
        predicate = T.build_filter(status, assignee_id, priority)
        return _safe(lambda: Ok(T.sort_tasks(T.select(self._repo.list_tasks(project_id), predicate))))

    @logged
    def pending_by_member(self, project_id: int) -> Result:
        return _safe(lambda: Ok(T.pending_by_member(
            self._repo.list_tasks(project_id), self._repo.list_members(project_id))))
