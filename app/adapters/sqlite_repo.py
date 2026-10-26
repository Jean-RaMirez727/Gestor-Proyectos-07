"""Adaptador SQLite. Cada operación escrita es una transacción (commit o rollback)."""
import functools
import sqlite3
import threading
from dataclasses import replace

from app.domain.models import Member, Priority, Project, Status, Task, WorkPackage
from app.ports.repository import PersistenceError

SCHEMA = """
CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS member (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    UNIQUE (project_id, name)
);
CREATE TABLE IF NOT EXISTS package (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES package(id) ON DELETE CASCADE,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    package_id INTEGER NOT NULL REFERENCES package(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    assignee_id INTEGER REFERENCES member(id) ON DELETE SET NULL,
    priority TEXT NOT NULL CHECK (priority IN ('Baja','Media','Alta')),
    status TEXT NOT NULL CHECK (status IN ('Pendiente','En progreso','En revisión','Terminada'))
);
"""


def _guard(method):
    """Convierte sqlite3.Error en PersistenceError (error de infraestructura)."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except sqlite3.Error as exc:
            raise PersistenceError(f"Error de base de datos: {exc}") from exc
    return wrapper


class SQLiteRepository:
    def __init__(self, path: str = "gestor.db"):
        self._lock = threading.RLock()
        try:
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.execute("PRAGMA foreign_keys = ON")
            with self._conn:
                self._conn.executescript(SCHEMA)
        except sqlite3.Error as exc:
            raise PersistenceError(f"No se pudo inicializar la base de datos: {exc}") from exc

    def close(self) -> None:
        self._conn.close()

    # --- helpers ---
    def _insert(self, sql: str, params: tuple) -> int:
        with self._lock, self._conn:  # transacción: commit o rollback
            return self._conn.execute(sql, params).lastrowid

    def _all(self, sql: str, params: tuple = ()) -> list:
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    def _one(self, sql: str, params: tuple = ()):
        with self._lock:
            return self._conn.execute(sql, params).fetchone()

    # --- proyectos ---
    @_guard
    def add_project(self, p: Project) -> Project:
        return replace(p, id=self._insert("INSERT INTO project(name, description) VALUES (?, ?)", (p.name, p.description)))

    @_guard
    def get_project(self, project_id: int) -> Project | None:
        row = self._one("SELECT id, name, description FROM project WHERE id = ?", (project_id,))
        return Project(*row) if row else None

    @_guard
    def list_projects(self) -> tuple[Project, ...]:
        return tuple(Project(*r) for r in self._all("SELECT id, name, description FROM project ORDER BY name"))

    # --- integrantes ---
    @_guard
    def add_member(self, m: Member) -> Member:
        return replace(m, id=self._insert("INSERT INTO member(project_id, name) VALUES (?, ?)", (m.project_id, m.name)))

    @_guard
    def list_members(self, project_id: int) -> tuple[Member, ...]:
        rows = self._all("SELECT id, project_id, name FROM member WHERE project_id = ? ORDER BY name", (project_id,))
        return tuple(Member(*r) for r in rows)

    # --- EDT ---
    @_guard
    def add_package(self, p: WorkPackage) -> WorkPackage:
        return replace(p, id=self._insert(
            "INSERT INTO package(project_id, parent_id, name) VALUES (?, ?, ?)", (p.project_id, p.parent_id, p.name)))

    @_guard
    def list_packages(self, project_id: int) -> tuple[WorkPackage, ...]:
        rows = self._all("SELECT id, project_id, name, parent_id FROM package WHERE project_id = ?", (project_id,))
        return tuple(WorkPackage(*r) for r in rows)

    # --- tareas ---
    @staticmethod
    def _task(r) -> Task:
        return Task(r[0], r[1], r[2], r[3], r[4], Priority(r[5]), Status(r[6]))

    @_guard
    def add_task(self, t: Task) -> Task:
        new_id = self._insert(
            "INSERT INTO task(project_id, package_id, title, assignee_id, priority, status) VALUES (?,?,?,?,?,?)",
            (t.project_id, t.package_id, t.title, t.assignee_id, t.priority.value, t.status.value))
        return replace(t, id=new_id)

    _TASK_COLS = "id, project_id, package_id, title, assignee_id, priority, status"

    @_guard
    def get_task(self, task_id: int) -> Task | None:
        row = self._one(f"SELECT {self._TASK_COLS} FROM task WHERE id = ?", (task_id,))
        return self._task(row) if row else None

    @_guard
    def list_tasks(self, project_id: int) -> tuple[Task, ...]:
        return tuple(self._task(r) for r in self._all(
            f"SELECT {self._TASK_COLS} FROM task WHERE project_id = ?", (project_id,)))

    @_guard
    def update_task(self, t: Task) -> Task:
        with self._lock, self._conn:
            cur = self._conn.execute(
                "UPDATE task SET title=?, assignee_id=?, priority=?, status=? WHERE id=?",
                (t.title, t.assignee_id, t.priority.value, t.status.value, t.id))
            if cur.rowcount == 0:
                raise PersistenceError(f"La tarea {t.id} ya no existe.")
        return t
