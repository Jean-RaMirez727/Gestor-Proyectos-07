from typing import Sequence

from app.core.result import Err, Ok, Result
from app.domain.errors import ValidationError
from app.domain.models import NodoWBS


def crear_nodo_wbs(
    id: str,
    codigo: str,
    nombre: str,
    padre_id: str | None = None,
    es_paquete_trabajo: bool = False,
) -> Result[NodoWBS, ValidationError]:
    cod = (codigo or "").strip()
    nom = (nombre or "").strip()
    if not cod:
        return Err(ValidationError("El código EDT (WBS) es obligatorio (ej: 1.1)."))
    if not nom:
        return Err(ValidationError("El nombre del entregable no puede estar vacío."))

    return Ok(
        NodoWBS(
            id=id,
            codigo=cod,
            nombre=nom,
            padre_id=padre_id,
            es_paquete_trabajo=es_paquete_trabajo,
        )
    )


def ordenar_nodos_por_codigo(nodos: Sequence[NodoWBS]) -> tuple[NodoWBS, ...]:
    """Ordenamiento funcional usando tuplas y comparación jerárquica."""
    def clave(nodo: NodoWBS):
        try:
            return [int(p) for p in nodo.codigo.split(".") if p.isdigit()]
        except ValueError:
            return [0]

    return tuple(sorted(nodos, key=clave))


def obtener_hijos(nodos: Sequence[NodoWBS], padre_id: str | None) -> tuple[NodoWBS, ...]:
    return tuple(n for n in nodos if n.padre_id == padre_id)