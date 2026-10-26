from app.core.result import Err, Ok
from app.core.tasks import (
    aplicar_filtro,
    crear_tarea,
    filtrar_por_estado,
    mover_tarea,
    validar_transicion_kanban,
)
from app.domain.errors import TransitionError, ValidationError
from app.domain.models import EstadoKanban, Prioridad, Tarea


def test_crear_tarea_exitoso():
    res = crear_tarea("T1", "WBS-1.1", "Diseñar base de datos")
    assert isinstance(res, Ok)
    assert res.value.titulo == "Diseñar base de datos"
    assert res.value.estado == EstadoKanban.PENDIENTE


def test_crear_tarea_falla_titulo_vacio():
    res = crear_tarea("T2", "WBS-1.1", "   ")
    assert isinstance(res, Err)
    assert isinstance(res.error, ValidationError)


def test_mover_tarea_transicion_valida():
    tarea = Tarea("T1", "WBS-1", "API", "", Prioridad.ALTA, EstadoKanban.PENDIENTE)
    res = mover_tarea(tarea, EstadoKanban.EN_PROGRESO)
    assert isinstance(res, Ok)
    assert res.value.estado == EstadoKanban.EN_PROGRESO
    # Inmutabilidad: la tarea original no muta
    assert tarea.estado == EstadoKanban.PENDIENTE


def test_mover_tarea_transicion_invalida_retorna_err():
    tarea = Tarea("T1", "WBS-1", "API", "", Prioridad.ALTA, EstadoKanban.PENDIENTE)
    res = mover_tarea(tarea, EstadoKanban.TERMINADA)
    assert isinstance(res, Err)
    assert isinstance(res.error, TransitionError)


def test_filtrar_por_estado_closure():
    t1 = Tarea("1", "W1", "A", "", Prioridad.BAJA, EstadoKanban.PENDIENTE)
    t2 = Tarea("2", "W1", "B", "", Prioridad.ALTA, EstadoKanban.TERMINADA)

    filtro = filtrar_por_estado(EstadoKanban.PENDIENTE)
    resultado = aplicar_filtro([t1, t2], filtro)
    assert len(resultado) == 1
    assert resultado[0].id == "1"