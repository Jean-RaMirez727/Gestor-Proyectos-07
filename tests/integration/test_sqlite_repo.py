import sqlite3
import unittest
from dataclasses import replace

from app.adapters.sqlite_repo import SQLiteRepository
from app.core.result import Err, Ok
from app.domain.errors import InvalidTransition, NotFound, PersistenceFailure
from app.domain.models import Member, Priority, Project, Status, Task, WorkPackage
from app.ports.repository import PersistenceError
from app.ui.service import AppService


class RepoTests(unittest.TestCase):
    def setUp(self):
        self.repo = SQLiteRepository(":memory:")  # base en memoria
        self.project = self.repo.add_project(Project(None, "P"))
        self.package = self.repo.add_package(WorkPackage(None, self.project.id, "Diseño"))

    def tearDown(self):
        self.repo.close()

    def test_roundtrip(self):
        m = self.repo.add_member(Member(None, self.project.id, "Ana"))
        t = self.repo.add_task(Task(None, self.project.id, self.package.id, "T", m.id, Priority.ALTA, Status.PENDIENTE))
        self.assertEqual(self.repo.get_task(t.id), t)
        self.assertEqual(self.repo.list_tasks(self.project.id), (t,))
        self.assertIsNone(self.repo.get_task(999))
        updated = self.repo.update_task(replace(t, status=Status.EN_PROGRESO))
        self.assertEqual(self.repo.get_task(t.id), updated)

    def test_failed_write_leaves_no_partial_data(self):
        self.repo.add_member(Member(None, self.project.id, "Ana"))
        with self.assertRaises(PersistenceError):
            self.repo.add_member(Member(None, self.project.id, "Ana"))  # viola UNIQUE
        self.assertEqual(len(self.repo.list_members(self.project.id)), 1)

    def test_foreign_key_enforced(self):
        with self.assertRaises(PersistenceError):
            self.repo.add_task(Task(None, self.project.id, 999, "T", None, Priority.BAJA, Status.PENDIENTE))
        self.assertEqual(self.repo.list_tasks(self.project.id), ())

    def test_update_missing_task(self):
        with self.assertRaises(PersistenceError):
            self.repo.update_task(Task(77, self.project.id, self.package.id, "x", None, Priority.BAJA, Status.PENDIENTE))


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = SQLiteRepository(":memory:")
        self.svc = AppService(self.repo)
        self.pid = self.svc.create_project("P").value.id
        self.pkg = self.svc.add_package(self.pid, "Diseño", None).value.id

    def test_flow_and_invalid_transition_keeps_state(self):
        t = self.svc.add_task(self.pid, self.pkg, "Hacer algo", Priority.MEDIA, None).value
        self.assertEqual(self.svc.move_task(t.id, Status.TERMINADA), Err(InvalidTransition(Status.PENDIENTE, Status.TERMINADA)))
        self.assertEqual(self.repo.get_task(t.id).status, Status.PENDIENTE)
        self.assertIsInstance(self.svc.move_task(t.id, Status.EN_PROGRESO), Ok)
        self.assertEqual(self.repo.get_task(t.id).status, Status.EN_PROGRESO)

    def test_missing_entities(self):
        self.assertEqual(self.svc.move_task(123, Status.EN_PROGRESO), Err(NotFound("tarea", 123)))
        self.assertEqual(self.svc.get_project(123), Err(NotFound("proyecto", 123)))

    def test_persistence_error_becomes_err(self):
        self.repo.close()
        self.assertIsInstance(self.svc.list_projects().error, PersistenceFailure)


if __name__ == "__main__":
    unittest.main()
