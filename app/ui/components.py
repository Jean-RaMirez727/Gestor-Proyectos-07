"""Componentes ReactPy. Sólo coordinan eventos: las reglas viven en app.core."""

from pathlib import Path

from reactpy import component, hooks, html

from app.core import tasks as T
from app.core import wbs as W
from app.core.result import Err, Ok
from app.domain.models import Priority, Status
from app.ui.messages import to_message
from app.ui.service import AppService

STYLE = (Path(__file__).with_name("styles.css")).read_text(encoding="utf-8")

_STATUS_CLASS = {
    Status.PENDING: "pendiente",
    Status.IN_PROGRESS: "en-progreso",
    Status.IN_REVIEW: "en-revision",
    Status.DONE: "terminada",
}
_PRIORITY_CLASS = {
    Priority.LOW: "baja",
    Priority.MEDIUM: "media",
    Priority.HIGH: "alta",
}


def _value(result, default):
    """Extrae el valor de un Ok; ante Err devuelve un valor por defecto."""
    match result:
        case Ok(v):
            return v
        case Err():
            return default


def _field(label, control):
    return html.label(
        {"class_name": "field"},
        html.span({"class_name": "field__label"}, label),
        control,
    )


def _text(value, set_value, placeholder="", label=None):
    control = html.input(
        {
            "class_name": "input",
            "value": value,
            "placeholder": placeholder,
            "on_change": lambda e: set_value(e["target"]["value"]),
        }
    )
    return _field(label or placeholder, control)


def _select(value, set_value, options, label=""):
    control = html.select(
        {
            "class_name": "select",
            "value": value,
            "on_change": lambda e: set_value(e["target"]["value"]),
        },
        [html.option({"value": v, "key": v}, text) for v, text in options],
    )
    return _field(label, control)


def _tag(kind, css, text):
    return html.span({"class_name": f"tag tag--{kind}-{css}"}, text)


def _section(section_id, title, subtitle, *children):
    return html.section(
        {"id": section_id, "class_name": "card"},
        html.div(
            {"class_name": "card__header"},
            html.h2({"class_name": "section-title"}, title),
            (
                html.p({"class_name": "text-muted text-small"}, subtitle)
                if subtitle
                else []
            ),
        ),
        *children,
    )


def _opt_int(raw: str) -> int | None:
    return int(raw) if raw else None


@component
def TaskCard(task, package_name, member_name, on_move, on_assign, members):
    def mover(target):
        return lambda event: on_move(task.id, target)

    def reassign(event):
        on_assign(task.id, _opt_int(event["target"]["value"]))

    return html.article(
        {"class_name": "task"},
        html.div({"class_name": "task__title"}, task.title),
        html.div(
            {"class_name": "task__meta"},
            _tag("status", _STATUS_CLASS[task.status], task.status.value),
            _tag(
                "prio",
                _PRIORITY_CLASS[task.priority],
                f"Prioridad {task.priority.value}",
            ),
        ),
        html.div({"class_name": "task__line"}, f"EDT: {package_name}"),
        html.div({"class_name": "task__line"}, f"Responsable: {member_name}"),
        html.select(
            {
                "class_name": "select select--compact",
                "aria-label": "Responsable",
                "value": str(task.assignee_id or ""),
                "on_change": reassign,
            },
            html.option({"value": ""}, "Sin responsable"),
            [html.option({"value": str(m.id), "key": m.id}, m.name) for m in members],
        ),
        html.div(
            {"class_name": "task__actions"},
            [
                html.button(
                    {
                        "key": s.value,
                        "class_name": "btn btn--secondary btn--small",
                        "on_click": mover(s),
                    },
                    f"→ {s.value}",
                )
                for s in T.allowed_transitions(task.status)
            ],
        ),
    )


@component
def App(service: AppService):
    theme, set_theme = hooks.use_state("light")  # solo visual; dura la sesión
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
    tasks = (
        _value(
            service.tasks(
                project_id,
                Status(f_status) if f_status else None,
                _opt_int(f_member),
                Priority(f_priority) if f_priority else None,
            ),
            (),
        )
        if project
        else ()
    )
    pending = _value(service.pending_by_member(project_id), {}) if project else {}
    columns = T.board(tasks)
    filtering = bool(f_status or f_member or f_priority)
    pkg_options = [(str(p.id), "· " * d + p.name) for d, p in tree]

    # --- vista ---
    def shell(*content):
        nav_items = [("inicio", "▤", "Proyectos")]
        if project is not None:
            nav_items += [
                ("equipo", "☻", "Equipo"),
                ("edt", "☰", "EDT"),
                ("nueva-tarea", "＋", "Nueva tarea"),
                ("filtros", "⚲", "Filtros"),
                ("kanban", "▦", "Tablero Kanban"),
            ]
        dark = theme == "dark"
        return html.div(
            {"class_name": "app-shell", "data-theme": theme},
            html.style(STYLE),
            html.header(
                {"class_name": "topbar"},
                html.div(
                    {"class_name": "brand"},
                    html.span(
                        {"class_name": "brand__logo", "aria-hidden": "true"}, "G"
                    ),
                    html.span({"class_name": "brand__name"}, "Gestor de proyectos"),
                ),
                html.button(
                    {
                        "class_name": "btn btn--secondary btn--small",
                        "aria-pressed": str(dark).lower(),
                        "on_click": lambda e: set_theme("light" if dark else "dark"),
                    },
                    "☀ Modo claro" if dark else "☾ Modo oscuro",
                ),
            ),
            html.div(
                {"class_name": "layout"},
                html.aside(
                    {"class_name": "sidebar"},
                    html.nav(
                        {"class_name": "nav", "aria-label": "Secciones"},
                        [
                            html.a(
                                {"key": i, "href": f"#{i}", "class_name": "nav__link"},
                                html.span(
                                    {"class_name": "nav__icon", "aria-hidden": "true"},
                                    icon,
                                ),
                                label,
                            )
                            for i, icon, label in nav_items
                        ],
                    ),
                ),
                html.main(
                    {"class_name": "main"},
                    html.div({"class_name": "main__inner"}, *content),
                ),
            ),
        )

    notice = (
        html.div(
            {
                "class_name": f"alert alert--{message[0]}",
                "role": "alert" if message[0] == "error" else "status",
            },
            html.span(
                {"class_name": "alert__icon", "aria-hidden": "true"},
                "✓" if message[0] == "ok" else "✕",
            ),
            message[1],
        )
        if message[1]
        else []
    )
    header = html.section(
        {"id": "inicio", "class_name": "card"},
        html.div(
            {"class_name": "card__header"},
            html.h1({"class_name": "page-title"}, "Gestor de proyectos: EDT + Kanban"),
            html.p(
                {"class_name": "text-muted"},
                (
                    "Aún no hay proyectos."
                    if not projects
                    else (
                        project.description
                        if project
                        else "Selecciona o crea un proyecto para comenzar."
                    )
                ),
            ),
        ),
        notice,
        html.div(
            {"class_name": "form-grid"},
            _select(
                str(project_id or ""),
                lambda v: set_project_id(_opt_int(v)),
                [("", "— Selecciona un proyecto —")]
                + [(str(p.id), p.name) for p in projects],
                "Proyecto",
            ),
            _text(p_name, set_p_name, "Nuevo proyecto"),
            _text(p_desc, set_p_desc, "Descripción"),
            html.button(
                {
                    "class_name": "btn btn--primary",
                    "on_click": lambda e: run(
                        service.create_project(p_name, p_desc),
                        "Proyecto creado.",
                        lambda created: (
                            set_project_id(created.id),
                            set_p_name(""),
                            set_p_desc(""),
                        ),
                    ),
                },
                "Crear proyecto",
            ),
        ),
    )
    if project is None:
        return shell(header)

    team = _section(
        "equipo",
        "Equipo",
        "Integrantes del proyecto y su carga pendiente.",
        html.div(
            {"class_name": "form-grid"},
            _text(m_name, set_m_name, "Nombre del integrante"),
            html.button(
                {
                    "class_name": "btn btn--primary",
                    "on_click": lambda e: run(
                        service.add_member(project_id, m_name),
                        "Integrante registrado.",
                        lambda _: set_m_name(""),
                    ),
                },
                "Agregar",
            ),
        ),
        (
            html.div(
                {"class_name": "table-wrap", "style": {"marginTop": "16px"}},
                html.table(
                    {"class_name": "table"},
                    html.thead(
                        html.tr(
                            html.th("Integrante"),
                            html.th({"class_name": "num"}, "Tareas pendientes"),
                        )
                    ),
                    html.tbody(
                        [
                            html.tr(
                                {"key": m.id},
                                html.td(m.name),
                                html.td(
                                    {"class_name": "num"}, str(pending.get(m.id, 0))
                                ),
                            )
                            for m in members
                        ]
                    ),
                ),
            )
            if members
            else html.p(
                {"class_name": "empty", "style": {"marginTop": "16px"}},
                "Sin integrantes.",
            )
        ),
    )
    wbs = _section(
        "edt",
        "EDT (paquetes de trabajo)",
        "Estructura de desglose del trabajo.",
        html.div(
            {"class_name": "form-grid"},
            _text(k_name, set_k_name, "Nuevo paquete"),
            _select(
                k_parent,
                set_k_parent,
                [("", "(entregable raíz)")] + pkg_options,
                "Paquete padre",
            ),
            html.button(
                {
                    "class_name": "btn btn--primary",
                    "on_click": lambda e: run(
                        service.add_package(project_id, k_name, _opt_int(k_parent)),
                        "Paquete agregado.",
                        lambda _: set_k_name(""),
                    ),
                },
                "Agregar",
            ),
        ),
        (
            html.ul(
                {"class_name": "tree", "style": {"marginTop": "16px"}},
                [
                    html.li(
                        {
                            "key": p.id,
                            "class_name": "tree__item",
                            "style": {"marginLeft": f"{d * 1.5}rem"},
                        },
                        p.name,
                    )
                    for d, p in tree
                ],
            )
            if tree
            else html.p(
                {"class_name": "empty", "style": {"marginTop": "16px"}},
                "La EDT está vacía.",
            )
        ),
    )
    new_task = _section(
        "nueva-tarea",
        "Nueva tarea",
        "Registra el trabajo dentro de un paquete de la EDT.",
        html.div(
            {"class_name": "form-grid"},
            _text(t_title, set_t_title, "Título"),
            _select(t_pkg, set_t_pkg, [("", "— Paquete —")] + pkg_options, "Paquete"),
            _select(
                t_member,
                set_t_member,
                [("", "Sin responsable")] + [(str(m.id), m.name) for m in members],
                "Responsable",
            ),
            _select(
                t_prio, set_t_prio, [(p.value, p.value) for p in Priority], "Prioridad"
            ),
            html.button(
                {
                    "class_name": "btn btn--primary",
                    "on_click": lambda e: run(
                        service.add_task(
                            project_id,
                            _opt_int(t_pkg),
                            t_title,
                            Priority(t_prio),
                            _opt_int(t_member),
                        ),
                        "Tarea creada.",
                        lambda _: set_t_title(""),
                    ),
                },
                "Crear tarea",
            ),
        ),
    )
    filters = _section(
        "filtros",
        "Filtros",
        "Acota las tareas que se muestran en el tablero.",
        html.div(
            {"class_name": "form-grid"},
            _select(
                f_status,
                set_f_status,
                [("", "Todos los estados")] + [(s.value, s.value) for s in Status],
                "Estado",
            ),
            _select(
                f_member,
                set_f_member,
                [("", "Todos los responsables")]
                + [(str(m.id), m.name) for m in members],
                "Responsable",
            ),
            _select(
                f_priority,
                set_f_priority,
                [("", "Todas las prioridades")]
                + [(p.value, p.value) for p in Priority],
                "Prioridad",
            ),
        ),
    )
    empty_text = (
        "No hay tareas que coincidan con los filtros."
        if filtering and not tasks
        else "No hay tareas todavía." if not tasks else ""
    )
    kanban = _section(
        "kanban",
        "Tablero Kanban",
        "",
        (
            html.p(
                {"class_name": "empty", "style": {"marginBottom": "16px"}}, empty_text
            )
            if empty_text
            else []
        ),
        html.div(
            {"class_name": "board"},
            [
                html.div(
                    {"class_name": "column", "key": s.value},
                    html.div(
                        {"class_name": "column__header"},
                        html.h3({"class_name": "column__title"}, s.value),
                        html.span(
                            {"class_name": "column__count"}, str(len(columns[s]))
                        ),
                    ),
                    [
                        TaskCard(
                            t,
                            pkg_names.get(t.package_id, "?"),
                            member_names.get(t.assignee_id, "—"),
                            lambda tid, target: run(
                                service.move_task(tid, target), "Tarea movida."
                            ),
                            lambda tid, mid: run(
                                service.assign_task(tid, mid),
                                "Responsable actualizado.",
                            ),
                            members,
                            key=t.id,
                        )
                        for t in columns[s]
                    ],
                )
                for s in Status
            ],
        ),
    )
    return shell(header, team, wbs, new_task, filters, kanban)
