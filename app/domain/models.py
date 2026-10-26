from dataclasses import dataclass
from enum import Enum
from typing import Optional

# =========================================================
# Enums (únicos; los nombres en español son alias)
# =========================================================


class Priority(str, Enum):
    LOW = "Baja"
    MEDIUM = "Media"
    HIGH = "Alta"

    # Nombres alternativos en español
    BAJA = "Baja"
    MEDIA = "Media"
    ALTA = "Alta"


class Status(str, Enum):
    PENDING = "Pendiente"
    IN_PROGRESS = "En progreso"
    IN_REVIEW = "En revisión"
    DONE = "Terminada"

    # Nombres alternativos en español
    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    EN_REVISION = "En revisión"
    TERMINADA = "Terminada"


# Un solo enum por concepto: los nombres en español son alias de los mismos
# valores, así que `Status.PENDIENTE is EstadoKanban.PENDIENTE`.
EstadoKanban = Status
Prioridad = Priority


# =========================================================
# Modelos de dominio existentes (en español)
# =========================================================


@dataclass(frozen=True, slots=True)
class Integrante:
    id: str
    nombre: str
    rol: str


@dataclass(frozen=True, slots=True)
class Tarea:
    id: str
    nodo_wbs_id: str
    titulo: str
    descripcion: str
    prioridad: Prioridad
    estado: EstadoKanban
    responsable_id: Optional[str] = None


@dataclass(frozen=True, slots=True)
class NodoWBS:
    """Elemento de la Estructura de Desglose del Trabajo (EDT/WBS)."""

    id: str
    codigo: str
    nombre: str
    padre_id: Optional[str] = None
    es_paquete_trabajo: bool = False


# =========================================================
# Modelos compatibles con el repositorio SQLite
# =========================================================


@dataclass(frozen=True, slots=True)
class Project:
    id: int
    name: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class Member:
    id: int
    project_id: int
    name: str


@dataclass(frozen=True, slots=True)
class WorkPackage:
    # El orden coincide con el SELECT de list_packages()
    id: int
    project_id: int
    name: str
    parent_id: Optional[int] = None


@dataclass(frozen=True, slots=True)
class Task:
    # El orden coincide con el SELECT de tareas de SQLite
    id: int
    project_id: int
    package_id: int
    title: str
    assignee_id: Optional[int]
    priority: Priority
    status: Status
