from app.core import tasks as T
from app.core import wbs as W
from app.core.result import Err, Ok, bind, map_ok
from app.domain.errors import InvalidTransition, NotFound, ValidationError
from app.domain.models import Member, Priority, Status, Task, WorkPackage

PKGS = (WorkPackage(1, 1, "Raíz"), WorkPackage(2, 1, "Hijo", 1))
MEMBERS = (Member(1, 1, "Ana"),)


def task(status=Status.PENDING, assignee=None, prio=Priority.MEDIUM, id=1):
    return Task(id, 1, 1, "T", assignee, prio, status)


def test_transiciones_validas_e_invalidas():
    assert T.change_status(task(), Status.IN_PROGRESS) == Ok(task(Status.IN_PROGRESS))
    assert T.change_status(task(), Status.DONE) == Err(InvalidTransition(Status.PENDING, Status.DONE))
    assert isinstance(T.change_status(task(Status.DONE), Status.IN_PROGRESS), Ok)  # reabrir


def test_create_task_valida():
    assert isinstance(T.create_task(1, 1, "  ", Priority.LOW, None, PKGS, MEMBERS).error, ValidationError)
    assert T.create_task(1, 9, "x", Priority.LOW, None, PKGS, MEMBERS) == Err(NotFound("paquete", 9))
    assert T.create_task(1, 1, "x", Priority.LOW, 9, PKGS, MEMBERS) == Err(NotFound("integrante", 9))
    assert T.create_task(1, 1, " x ", Priority.LOW, 1, PKGS, MEMBERS).value.title == "x"


def test_assign_y_filtros():
    assert T.assign(task(), 1, MEMBERS).value.assignee_id == 1
    assert T.assign(task(), 5, MEMBERS) == Err(NotFound("integrante", 5))
    ts = [task(id=1), task(Status.DONE, 1, id=2)]
    assert len(T.select(ts, T.build_filter(status=Status.DONE))) == 1
    assert len(T.select(ts, T.build_filter())) == 2
    assert T.find_by_id(ts, 99) is None
    assert T.pending_by_member(ts, MEMBERS) == {1: 0}
    assert [len(v) for v in T.board(ts).values()] == [1, 0, 0, 1]


def test_wbs_y_result():
    assert [(d, p.name) for d, p in W.flatten_tree(PKGS)] == [(0, "Raíz"), (1, "Hijo")]
    assert W.create_package(1, "Otro", 9, PKGS) == Err(NotFound("paquete padre", 9))
    assert isinstance(W.create_member(1, "ana", MEMBERS).error, ValidationError)
    assert map_ok(Ok(1), lambda x: x + 1) == Ok(2)
    assert bind(Err("e"), lambda x: Ok(x)) == Err("e")
