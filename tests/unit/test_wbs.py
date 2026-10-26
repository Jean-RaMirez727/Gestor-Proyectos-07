from app.core.result import Err, Ok
from app.core.wbs import crear_nodo_wbs, obtener_hijos, ordenar_nodos_por_codigo
from app.domain.models import NodoWBS


def test_crear_nodo_wbs_exitoso():
    res = crear_nodo_wbs("N1", "1.1", "Planificación")
    assert isinstance(res, Ok)
    assert res.value.codigo == "1.1"


def test_crear_nodo_wbs_falla_sin_codigo():
    res = crear_nodo_wbs("N2", "", "Planificación")
    assert isinstance(res, Err)


def test_ordenar_nodos_por_codigo():
    n1 = NodoWBS("1", "1.2", "Módulo 2")
    n2 = NodoWBS("2", "1.1", "Módulo 1")
    n3 = NodoWBS("3", "1.10", "Módulo 10")

    ordenados = ordenar_nodos_por_codigo([n1, n2, n3])
    codigos = [n.codigo for n in ordenados]
    assert codigos == ["1.1", "1.2", "1.10"]


def test_obtener_hijos():
    padre = NodoWBS("P1", "1", "Proyecto")
    hijo = NodoWBS("H1", "1.1", "Entregable", padre_id="P1")

    hijos = obtener_hijos([padre, hijo], padre_id="P1")
    assert len(hijos) == 1
    assert hijos[0].id == "H1"