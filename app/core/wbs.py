"""Núcleo funcional de la EDT/WBS: funciones puras, sin I/O."""
from dataclasses import replace
from typing import Sequence

from app.core.result import Err, Ok, Result
from app.domain.errors import NotFound, ValidationError
from app.domain.models import Member, NodoWBS, Project, WorkPackage

MAX_NOMBRE = 100


# ---------------------------------------------------------------------------
# Proyectos, integrantes y paquetes de trabajo (modelo usado por la aplicación)
# ---------------------------------------------------------------------------
def _clean_name(raw: str | None, label: str) -> Result:
    name = (raw or "").strip()
    match name:
        case "":
            return Err(ValidationError(f"El nombre {label} no puede estar vacío."))
        case _ if len(name) > MAX_NOMBRE:
            return Err(ValidationError(f"El nombre {label} supera el límite de {MAX_NOMBRE} caracteres."))
        case _:
            return Ok(name)


def create_project(name: str, description: str = "") -> Result:
    match _clean_name(name, "del proyecto"):
        case Ok(clean):
            return Ok(Project(None, clean, (description or "").strip()))
        case err:
            return err


def create_member(project_id: int, name: str, existing: Sequence[Member]) -> Result:
    match _clean_name(name, "del integrante"):
        case Ok(clean):
            if any(m.name.casefold() == clean.casefold() for m in existing):
                return Err(ValidationError(f"Ya existe un integrante llamado «{clean}» en este proyecto."))
            return Ok(Member(None, project_id, clean))
        case err:
            return err


def create_package(project_id: int, name: str, parent_id: int | None,
                   existing: Sequence[WorkPackage]) -> Result:
    match _clean_name(name, "del paquete"):
        case Ok(clean):
            if parent_id is not None and all(p.id != parent_id for p in existing):
                return Err(NotFound("paquete padre", parent_id))
            if any(p.parent_id == parent_id and p.name.casefold() == clean.casefold() for p in existing):
                return Err(ValidationError(f"Ya existe un paquete «{clean}» en ese nivel de la EDT."))
            return Ok(WorkPackage(None, project_id, clean, parent_id))
        case err:
            return err


def rename_package(package: WorkPackage, new_name: str) -> Result:
    """Devuelve un paquete nuevo con otro nombre (el original no cambia)."""
    match _clean_name(new_name, "del paquete"):
        case Ok(clean):
            return Ok(replace(package, name=clean))
        case err:
            return err


def flatten_tree(packages: Sequence[WorkPackage]) -> list[tuple[int, WorkPackage]]:
    """Recorrido en profundidad: lista de (nivel, paquete) lista para dibujar la EDT."""
    ids = {p.id for p in packages}
    children: dict[int | None, list[WorkPackage]] = {}
    for p in packages:
        # Un paquete cuyo padre no existe se trata como raíz para no perderlo.
        key = p.parent_id if p.parent_id in ids else None
        children.setdefault(key, []).append(p)

    def walk(parent: int | None, depth: int, seen: frozenset) -> list[tuple[int, WorkPackage]]:
        out: list[tuple[int, WorkPackage]] = []
        for p in sorted(children.get(parent, ()), key=lambda x: (x.name.casefold(), x.id)):
            if p.id in seen:  # protección ante ciclos
                continue
            out.append((depth, p))
            out.extend(walk(p.id, depth + 1, seen | {p.id}))
        return out

    return walk(None, 0, frozenset())


# ---------------------------------------------------------------------------
# Modelo EDT con códigos (NodoWBS)
# ---------------------------------------------------------------------------
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
        return [int(p) for p in nodo.codigo.split(".") if p.isdigit()]

    return tuple(sorted(nodos, key=clave))


def obtener_hijos(nodos: Sequence[NodoWBS], padre_id: str | None) -> tuple[NodoWBS, ...]:
    return tuple(n for n in nodos if n.padre_id == padre_id)
