"""Componentes ReactPy. Sólo coordinan eventos: las reglas viven en app.core."""
from reactpy import component, hooks, html

from app.core import tasks as T
from app.core import wbs as W
from app.core.result import Err, Ok
from app.domain.models import Priority, Status
from app.ui.messages import to_message
from app.ui.service import AppService

STYLE = """
body{font-family:system-ui,sans-serif;margin:1.5rem;background:#f5f6f8;color:#222}
section{background:#fff;border-radius:8px;padding:1rem;margin-bottom:1rem;box-shadow:0 1px 3px #0002}
h1,h2,h3{margin:.2rem 0 .6rem} input,select,button{margin:0 .4rem .4rem 0;padding:.35rem .5rem}
.row{display:flex;flex-wrap:wrap;align-items:center}
.board{display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem}
.col{background:#eef0f4;border-radius:6px;padding:.6rem;min-height:6rem}
.card{background:#fff;border-radius:6px;padding:.5rem;margin-bottom:.5rem;box-shadow:0 1px 2px #0003}
.ok{color:#17692f}.error{color:#a31515}.muted{color:#666;font-size:.85rem}
"""


def _value(result, default):
    """Extrae el valor de un Ok; ante Err devuelve un valor por defecto."""
    match result:
        case Ok(v):
            return v
        case Err():
            return default


def _text(value, set_value, placeholder=""):
    return html.input({"value": value, "placeholder": placeholder,
                       "on_change": lambda e: set_value(e["target"]["value"])})


def _select(value, set_value, options):
    return html.select({"value": value, "on_change": lambda e: set_value(e["target"]["value"])},
                       [html.option({"value": v, "key": v}, label) for v, label in options])


def _opt_int(raw: str) -> int | None:
    return int(raw) if raw else None


@component
def TaskCard(task, package_name, member_name, on_move, on_assign, members):
    def mover(target):
        return lambda event: on_move(task.id, target)

    def reassign(event):
        on_assign(task.id, _opt_int(event["target"]["value"]))

    return html.div(
        {"class_name": "card"},
        html.strong(task.title),
        html.div({"class_name": "muted"}, f"EDT: {package_name} · Prioridad: {task.priority.value}"),
        html.select({"value": str(task.assignee_id or ""), "on_change": reassign},
                    html.option({"value": ""}, "Sin responsable"),
                    [html.option({"value": str(m.id), "key": m.id}, m.name) for m in members]),
        html.div([html.button({"key": s.value, "on_click": mover(s)}, f"→ {s.value}")
                  for s in T.allowed_transitions(task.status)]),
    )


@component
def App(service: AppService):
    tick, set_tick = hooks.use_state(0)  # fuerza relectura tras cada cambio
    project_id, set_project_id = hooks.use_state(None)
    message, set_message = hooks.use_state(("", ""))
    f_status, set_f_status = hooks.use_state("")
    f_member, set_f_member = hooks.use_state("")
    f_priority, set_f_priority = hooks.use_state("")
    p_name, set_p_name = hooks.use_state("")
    p_desc, set_p_desc = hooks.use_state("")
    m_name, set_m_name = hooks.use_state("")
    k_name, set_k_name = hooks.use_state("")
    k_parent, set_k_parent = hooks.use_state("")
    t_title, set_t_title = hooks.use_state("")
    t_pkg, set_t_pkg = hooks.use_state("")
    t_member, set_t_member = hooks.use_state("")
    t_prio, set_t_prio = hooks.use_state(Priority.MEDIA.value)

    def run(result, ok_text, on_ok=lambda value: None):
        """Muestra el resultado de un caso de uso y refresca la vista."""
        match result:
            case Ok(value):
                on_ok(value)
                set_message(("ok", ok_text))
            case Err(error):
                set_message(("error", to_message(error)))
        set_tick(tick + 1)

    # --- lectura (la shell obtiene datos) ---
    projects = _value(service.list_projects(), ())
    project = _value(service.get_project(project_id), None) if project_id else None
    members = _value(service.members(project_id), ()) if project else ()
    packages = _value(service.packages(project_id), ()) if project else ()
    tree = W.flatten_tree(packages)
    pkg_names = {p.id: p.name for p in packages}
    member_names = {m.id: m.name for m in members}
    tasks = _value(service.tasks(
        project_id,
        Status(f_status) if f_status else None,
        _opt_int(f_member),
        Priority(f_priority) if f_priority else None), ()) if project else ()
    pending = _value(service.pending_by_member(project_id), {}) if project else {}
    columns = T.board(tasks)
    filtering = bool(f_status or f_member or f_priority)
    pkg_options = [(str(p.id), "· " * d + p.name) for d, p in tree]

    # --- vista ---
    header = html.section(
        html.h1("Gestor de proyectos: EDT + Kanban"),
        html.div({"class_name": message[0]}, message[1]),
        html.div({"class_name": "row"},
                 _select(str(project_id or ""), lambda v: set_project_id(_opt_int(v)),
                         [("", "— Selecciona un proyecto —")] + [(str(p.id), p.name) for p in projects]),
                 _text(p_name, set_p_name, "Nuevo proyecto"), _text(p_desc, set_p_desc, "Descripción"),
                 html.button({"on_click": lambda e: run(
                     service.create_project(p_name, p_desc), "Proyecto creado.",
                     lambda created: (set_project_id(created.id), set_p_name(""), set_p_desc("")))},
                     "Crear proyecto")),
        html.div({"class_name": "muted"}, "Aún no hay proyectos." if not projects else
                 (project.description if project else "")),
    )
    if project is None:
        return html.div(html.style(STYLE), header)

    team = html.section(
        html.h2("Equipo"),
        html.div({"class_name": "row"}, _text(m_name, set_m_name, "Nombre del integrante"),
                 html.button({"on_click": lambda e: run(service.add_member(project_id, m_name),
                                                        "Integrante registrado.",
                                                        lambda _: set_m_name(""))}, "Agregar")),
        html.ul([html.li({"key": m.id}, f"{m.name} — {pending.get(m.id, 0)} tareas pendientes")
                 for m in members]) if members else html.p({"class_name": "muted"}, "Sin integrantes."),
    )
    wbs = html.section(
        html.h2("EDT (paquetes de trabajo)"),
        html.div({"class_name": "row"}, _text(k_name, set_k_name, "Nuevo paquete"),
                 _select(k_parent, set_k_parent, [("", "(entregable raíz)")] + pkg_options),
                 html.button({"on_click": lambda e: run(
                     service.add_package(project_id, k_name, _opt_int(k_parent)),
                     "Paquete agregado.", lambda _: set_k_name(""))}, "Agregar")),
        html.ul([html.li({"key": p.id, "style": {"marginLeft": f"{d * 1.2}rem"}}, p.name) for d, p in tree])
        if tree else html.p({"class_name": "muted"}, "La EDT está vacía."),
    )
    new_task = html.section(
        html.h2("Nueva tarea"),
        html.div({"class_name": "row"}, _text(t_title, set_t_title, "Título"),
                 _select(t_pkg, set_t_pkg, [("", "— Paquete —")] + pkg_options),
                 _select(t_member, set_t_member, [("", "Sin responsable")] + [(str(m.id), m.name) for m in members]),
                 _select(t_prio, set_t_prio, [(p.value, p.value) for p in Priority]),
                 html.button({"on_click": lambda e: run(
                     service.add_task(project_id, _opt_int(t_pkg), t_title, Priority(t_prio), _opt_int(t_member)),
                     "Tarea creada.", lambda _: set_t_title(""))}, "Crear tarea")),
    )
    filters = html.section(
        html.h2("Filtros"),
        html.div({"class_name": "row"},
                 _select(f_status, set_f_status, [("", "Todos los estados")] + [(s.value, s.value) for s in Status]),
                 _select(f_member, set_f_member, [("", "Todos los responsables")] + [(str(m.id), m.name) for m in members]),
                 _select(f_priority, set_f_priority, [("", "Todas las prioridades")] + [(p.value, p.value) for p in Priority])),
    )
    kanban = html.section(
        html.h2("Tablero Kanban"),
        html.p({"class_name": "muted"}, "No hay tareas que coincidan con los filtros." if filtering and not tasks
               else "No hay tareas todavía." if not tasks else ""),
        html.div({"class_name": "board"}, [
            html.div({"class_name": "col", "key": s.value},
                     html.h3(f"{s.value} ({len(columns[s])})"),
                     [TaskCard(t, pkg_names.get(t.package_id, "?"), member_names.get(t.assignee_id, "—"),
                               lambda tid, target: run(service.move_task(tid, target), "Tarea movida."),
                               lambda tid, mid: run(service.assign_task(tid, mid), "Responsable actualizado."),
                               members, key=t.id) for t in columns[s]])
            for s in Status]),
    )
    return html.div(html.style(STYLE), header, team, wbs, new_task, filters, kanban)
