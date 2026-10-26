from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EstadoKanban(str, Enum):
    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    EN_REVISION = "En revisión"
    TERMINADA = "Terminada"


class Prioridad(str, Enum):
    BAJA = "Baja"
    MEDIA = "Media"
    ALTA = "Alta"


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