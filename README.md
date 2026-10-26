# Gestor de proyectos con EDT y Kanban

Aplicación web local para planificar un proyecto con una **EDT/WBS** (¿qué trabajo hay que hacer?) y dar seguimiento a sus tareas en un tablero **Kanban** (¿en qué estado está ese trabajo?).

Tecnologías: Python · ReactPy (interfaz) · FastAPI (sólo sirve e integra ReactPy, **no hay API REST propia**) · SQLite (persistencia local) · CSS propio, sin frameworks de interfaz.

---

## Cómo ejecutarla (un solo paso)

1. Instala **Python 3** (recomendado 3.14; sirve cualquier 3.10 o superior) desde <https://www.python.org>. Durante la instalación deja marcada la opción del lanzador `py`.
2. Haz **doble clic en `iniciar.bat`**.

Eso es todo. El archivo se encarga de:

- elegir la versión de Python disponible,
- crear el entorno virtual `.venv` si no existe (o recrearlo si está dañado),
- instalar las dependencias de `requirements.txt`,
- iniciar la aplicación y abrir el navegador en <http://127.0.0.1:8000>.

La primera vez tarda más porque descarga las dependencias (requiere internet); las siguientes veces arranca en pocos segundos. Para detener la aplicación, cierra la ventana negra de `iniciar.bat` (o pulsa `Ctrl + C`).

Los datos se guardan en `gestor.db`, en la carpeta del proyecto. Para empezar desde cero, cierra la aplicación y borra ese archivo; se vuelve a crear solo.

> Opcional (variables de entorno): `GESTOR_DB` cambia la ruta de la base de datos y `GESTOR_PORT` cambia el puerto (por defecto 8000).

### Cómo usarla

1. **Proyecto:** escribe un nombre y pulsa *Crear proyecto* (o elige uno existente en la lista).
2. **Equipo:** agrega a los integrantes.
3. **EDT:** crea entregables raíz y paquetes de trabajo anidados eligiendo el paquete padre.
4. **Nueva tarea:** define título, paquete de la EDT, responsable y prioridad.
5. **Tablero Kanban:** mueve cada tarea con los botones de la tarjeta (sólo aparecen los movimientos permitidos) y cambia su responsable desde la propia tarjeta.
6. **Filtros:** acota el tablero por estado, responsable o prioridad.
7. **Modo claro/oscuro:** botón en la barra superior (dura lo que dure la sesión del navegador).

### Ejecutar las pruebas (opcional)

Desde una terminal en la carpeta del proyecto:

```bat
.venv\Scripts\python.exe -m pytest
```

`tests/unit` prueba el núcleo sin ReactPy, FastAPI ni archivos; `tests/integration` prueba el adaptador SQLite y el servicio con una base **en memoria** (nunca toca `gestor.db`). Estado actual: **20 pruebas, todas pasan**.

---

## Estructura

```text
iniciar.bat        Arranque con doble clic
app/
  domain/    models.py (dataclasses inmutables, enums), errors.py (errores como valores)
  core/      result.py, tasks.py, wbs.py           -> FUNCTIONAL CORE (puro)
  ports/     repository.py (Protocol + PersistenceError)
  adapters/  sqlite_repo.py, instrumentation.py    -> efectos externos
  ui/        service.py, messages.py, components.py, styles.css  -> IMPERATIVE SHELL
  main.py    ensamble de FastAPI + ReactPy
tests/
  unit/        núcleo funcional
  integration/ adaptador SQLite y servicio
```

Flujo de cada acción: `evento ReactPy → el servicio lee datos → función pura del core → el servicio guarda → la interfaz se actualiza`.
El núcleo (`domain/` y `core/`) no importa ReactPy, FastAPI, `sqlite3` ni el sistema de archivos.

**Reglas Kanban** (`core/tasks.py::ALLOWED_TRANSITIONS`):
Pendiente → En progreso → En revisión → Terminada. Se puede retroceder un paso (En progreso → Pendiente, En revisión → En progreso) y reabrir (Terminada → En progreso). Cualquier otro movimiento, incluido «mover al mismo estado», se rechaza con un mensaje y sin modificar la tarea.

---

## Cumplimiento de lo que pide el enunciado

### Alcance mínimo

| # | Requisito | Estado | Dónde |
|---|---|---|---|
| 1 | Crear y consultar un proyecto | Cumple | `core/wbs.py::create_project`, `ui/service.py::create_project / get_project / list_projects` |
| 2 | Registrar integrantes | Cumple (no admite nombres repetidos en el proyecto) | `core/wbs.py::create_member` |
| 3 | Descomponer en entregables, paquetes y tareas | Cumple (EDT jerárquica con paquetes anidados; tareas dentro de un paquete) | `core/wbs.py::create_package`, `flatten_tree`; `core/tasks.py::create_task` |
| 4 | Asignar responsable, prioridad y estado | Cumple (el estado inicial es Pendiente y luego cambia por transiciones) | `core/tasks.py::create_task`, `assign` |
| 5 | Consultar tareas en un tablero Kanban | Cumple (4 columnas con contador) | `core/tasks.py::board`, `ui/components.py` |
| 6 | Cambiar estado con transición válida | Cumple | `core/tasks.py::change_status`, `ALLOWED_TRANSITIONS` |
| 7 | Filtrar por estado, responsable o prioridad | Cumple (se pueden combinar) | `core/tasks.py::build_filter`, `select` |
| 8 | Guardar y recuperar en SQLite | Cumple | `adapters/sqlite_repo.py` |
| 9 | Mensajes comprensibles (datos inválidos, sin resultados, fallos de persistencia) | Cumple | `ui/messages.py::to_message`; mensajes de «sin resultados» en `ui/components.py` |

### Arquitectura y calidad

| Requisito | Estado | Detalle |
|---|---|---|
| Núcleo sin ReactPy/FastAPI/archivos | Cumple | Sólo `core/` y `domain/` con lógica; las pruebas unitarias no los importan. |
| Sin API REST propia | Cumple | `main.py` sólo monta ReactPy sobre FastAPI. |
| Reglas fuera de los callbacks | Cumple | Los callbacks de `components.py` únicamente llaman al servicio y muestran el resultado. |
| Validar antes de guardar | Cumple | Las validaciones ocurren en `core/` y, si fallan, el servicio no llega a escribir. |
| Sin estado parcial ante una operación inválida | Cumple | Cada escritura SQLite es una transacción (`with conn:` → commit o rollback); hay pruebas (`test_failed_write_leaves_no_partial_data`, `test_flow_and_invalid_transition_keeps_state`). |
| Esquema SQLite controlado | Cumple | `CREATE TABLE IF NOT EXISTS`, claves foráneas activas y restricciones `CHECK`. |
| Pruebas del adaptador sin datos reales | Cumple | Usan `SQLiteRepository(":memory:")`. |
| Tablero coherente con el estado de cada tarea | Cumple | La vista se recalcula desde la base tras cada cambio. |
| Instrucciones de instalación y ejecución | Cumple | Este documento; basta con `iniciar.bat`. |

### Contenidos del curso: evidencias

| Contenido | Archivo · función | Cómo se aplica |
|---|---|---|
| Del cómo al qué | `core/tasks.py` · `ALLOWED_TRANSITIONS`, `board`, `pending_by_member` | Las reglas se declaran como datos y consultas («qué» transiciones existen, «qué» tareas hay en cada columna) en vez de bucles con banderas. |
| Pattern matching | `core/tasks.py` · `change_status`; `core/result.py` · `bind`, `map_ok`; `core/wbs.py` · `create_*`; `ui/messages.py` · `to_message`; `ui/components.py` · `run`, `_value` | `match/case` sobre pares (estado actual, destino), variantes `Ok/Err` y tipos de error. |
| Funciones de orden superior | `core/tasks.py` · `all_of`, `select`, `build_filter`; `core/result.py` · `bind`, `map_ok` | Reciben o devuelven funciones; `bind` encadena casos de uso que pueden fallar. |
| Lambdas y HOF | `core/tasks.py` · `sort_tasks` (clave de orden), `by_*` | Lambdas pequeñas para criterios de orden y filtro. Se usan funciones con nombre (`create_task`, `change_status`, `build_filter`) cuando hay validación o lógica que probar y documentar. |
| Closures | `core/tasks.py` · `by_status`, `by_assignee`, `by_priority` | Cada una captura un criterio inmutable y devuelve un predicado; no hay estado mutable capturado. |
| Inmutabilidad | `domain/models.py` (`frozen=True`); `change_status`, `assign`, `rename_package` | `dataclasses.replace` produce valores nuevos; `tests/unit/test_tasks.py` comprueba que la tarea original no cambia. |
| Pureza y efectos | Puras: todo `core/` y `domain/`. Shell: `ui/service.py` (lee/guarda), `ui/components.py` (estado visual), `adapters/` (SQLite, registro). | La shell lee → llama al core → guarda. |
| Ausencia de valor | `core/tasks.py` · `find_by_id` (devuelve `None`); `ui/service.py` · `_required` | `None` significa «no existe» y se convierte en `Err(NotFound(...))`; una lista vacía es un resultado válido distinto. |
| Manejo funcional de errores | `core/result.py`; `domain/errors.py`; `ui/service.py` · `_safe` | Validaciones y transiciones inválidas devuelven `Err(...)`. Las excepciones de SQLite se confinan en el adaptador y `_safe` las convierte en `Err(PersistenceFailure)`. |
| Decoradores | `adapters/instrumentation.py` · `@logged`; `adapters/sqlite_repo.py` · `@_guard` | `@logged` registra operación y duración de cada caso de uso, sin reglas de negocio. `@_guard` traduce `sqlite3.Error` a `PersistenceError`. |

### Limitaciones y puntos a tener en cuenta

- **Modelos duplicados:** además del modelo que usa la aplicación (`Project`, `Member`, `WorkPackage`, `Task`) existe un modelo en español (`Tarea`, `NodoWBS`, `crear_tarea`, `mover_tarea`…) que la interfaz no utiliza y que se conserva con sus pruebas unitarias. Conviene decidir en el equipo si se mantiene o se elimina antes de la entrega.
- **EDT sin edición en pantalla:** la interfaz permite crear paquetes, pero no renombrarlos ni eliminarlos. `core/wbs.py::rename_package` existe como función pura (actualiza sin mutar), aunque todavía no está conectada a la interfaz ni tiene prueba propia.
- **Tareas sin descripción:** el modelo de tarea guarda título, paquete, responsable, prioridad y estado; no hay campo de descripción.
- **Tema claro/oscuro:** no se recuerda al recargar la página (ReactPy no ofrece almacenamiento del navegador de forma directa).
- **Sin pruebas automáticas de la interfaz:** las pruebas cubren el núcleo, el adaptador SQLite y el servicio; los componentes ReactPy se verifican de forma manual.

### Entregables que dependen del equipo (no están en este repositorio)

Estos puntos del enunciado no pueden resolverse con código y quedan pendientes de completar por el equipo:

- [ ] Repositorio remoto con historial que muestre el aporte de cada integrante.
- [ ] PDF de presentación con enlaces clicables al repositorio y al video, y sección de contribuciones.
- [ ] Video de demostración en el que participen todos los integrantes.

---

## Uso de inteligencia artificial

Se usó IA como apoyo para revisar errores y mejorar la interfaz. Cada integrante debe poder explicar el código que presenta: dónde están las funciones puras, los efectos secundarios y las reglas de negocio (ver tablas anteriores).
