# Gestor de proyectos con EDT y Kanban

Aplicación web local (ReactPy + FastAPI + SQLite) para planificar un proyecto con una **EDT/WBS** y dar seguimiento a las tareas en un tablero **Kanban**. Diseñada con *Functional Core / Imperative Shell*.

## Instalación y ejecución (Python 3.10+)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.main               # o: uvicorn app.main:app --reload
```
Abrir <http://127.0.0.1:8000>. La base se guarda en `gestor.db` (cambiar con la variable `GESTOR_DB`).

## Pruebas

```bash
pytest                           # o: python -m unittest discover -s tests -t .
```
`tests/unit` prueba el núcleo sin ReactPy ni FastAPI; `tests/integration` usa SQLite en memoria.

## Arquitectura

```text
app/
  domain/    models.py (dataclasses inmutables, enums), errors.py (errores como valores)
  core/      result.py, tasks.py, wbs.py        -> FUNCTIONAL CORE (puro)
  ports/     repository.py (Protocol + PersistenceError)
  adapters/  sqlite_repo.py, instrumentation.py -> efectos externos
  ui/        service.py (coordina), messages.py, components.py -> IMPERATIVE SHELL
  main.py    ensamble FastAPI + ReactPy
```
Flujo: `evento ReactPy → service lee datos → función pura del core → service guarda → UI se actualiza`.
El core no importa ReactPy, FastAPI, sqlite3 ni el sistema de archivos.

**Transiciones Kanban** (`core/tasks.py::ALLOWED_TRANSITIONS`):
Pendiente → En progreso → En revisión → Terminada; se puede retroceder un paso (En progreso → Pendiente, En revisión → En progreso) y reabrir (Terminada → En progreso). Todo lo demás se rechaza.

## Evidencias de los contenidos del curso

| Contenido | Archivo · función | Cómo se aplica |
|---|---|---|
| Del cómo al qué | `core/tasks.py` · `ALLOWED_TRANSITIONS`, `board`, `pending_by_member` | Las reglas se declaran como datos/consultas (qué transiciones existen, cómo se agrupa) en vez de bucles con banderas. |
| Pattern matching | `core/tasks.py` · `change_status`; `core/wbs.py` · `create_*`; `ui/messages.py` · `to_message`; `ui/components.py` · `run` | `match/case` sobre pares (origen, destino), variantes `Ok/Err` y tipos de error. |
| Funciones de orden superior | `core/tasks.py` · `all_of`, `select`, `build_filter`; `core/result.py` · `bind`, `map_ok` | Reciben o devuelven funciones; `bind` compone casos de uso que pueden fallar. |
| Lambdas y HOF | `core/tasks.py` · `sort_tasks` (clave), `by_*` | Lambdas pequeñas para criterios de orden y filtro. Se usan funciones con nombre (`build_filter`, `create_task`) cuando hay lógica, validación o necesitan docstring/pruebas. |
| Closures | `core/tasks.py` · `by_status`, `by_assignee`, `by_priority` | Cada una captura un criterio inmutable y devuelve un predicado; no hay estado mutable capturado. |
| Inmutabilidad | `domain/models.py` (`frozen=True`); `change_status`, `assign`, `rename_package` | Se usa `dataclasses.replace` para producir valores nuevos; las pruebas verifican que el original no cambia. |
| Pureza y efectos | Puras: todo `core/` y `domain/`. Shell: `ui/service.py` (I/O con repositorio), `ui/components.py` (estado visual), `adapters/` (SQLite, logging). | La shell lee → llama al core → guarda. |
| Ausencia de valor | `core/tasks.py` · `find_by_id` (devuelve `None`); `ui/service.py` · `_required` | `None` = "no existe" y se convierte en `Err(NotFound(...))`; una lista vacía es un resultado válido distinto. |
| Manejo funcional de errores | `core/result.py`; `domain/errors.py`; `ui/service.py` · `_safe` | Validación y transiciones inválidas devuelven `Err(...)`. Las excepciones de SQLite se confinan al adaptador y `_safe` las convierte en `Err(PersistenceFailure)`. |
| Decoradores | `adapters/instrumentation.py` · `@logged`; `adapters/sqlite_repo.py` · `@_guard` | `@logged` registra operación y duración de cada caso de uso (preocupación transversal, sin reglas de negocio). `@_guard` traduce `sqlite3.Error` a `PersistenceError`. |

## Calidad y persistencia

- Datos validados en el core **antes** de guardar; una operación inválida no toca la base.
- Esquema creado con `CREATE TABLE IF NOT EXISTS`, claves foráneas y `CHECK` activos.
- Cada escritura corre en una transacción (`with conn:` → commit o rollback).
- Mensajes de usuario para: datos inválidos, transiciones no permitidas, entidades inexistentes, filtros sin resultados y fallos de base de datos.
