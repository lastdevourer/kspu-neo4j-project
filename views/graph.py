from __future__ import annotations

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from ui.components import (
    render_empty_state,
    render_fullscreen_dataframe_heading,
    render_fullscreen_html_heading,
    render_header,
    render_key_value_card,
    render_section_heading,
    require_service,
)
from ui.formatters import coauthor_graph_dataframe, department_collaboration_dataframe, graph_edges_dataframe
from utils.graph_visualization import (
    build_bipartite_graph_html,
    build_coauthor_graph_html,
    build_department_graph_html,
)


def _csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8-sig")


def _department_options(service) -> dict[str, str]:
    rows = service.get_departments()
    options = {"Усі кафедри": ""}
    for row in rows:
        faculty_name = str(row.get("faculty_name") or "").strip()
        label = f"{row['name']} — {faculty_name}" if faculty_name else str(row["name"])
        options[label] = row["code"]
    return options


def _faculty_options(service) -> dict[str, str]:
    rows = service.get_faculty_overview()
    options = {"Усі факультети": ""}
    for row in rows:
        options[str(row["name"])] = row["code"]
    return options


def _teacher_options(rows: list[dict[str, object]]) -> dict[str, str]:
    options: dict[str, str] = {}
    for row in rows:
        name = str(row.get("full_name") or "").strip()
        department_name = str(row.get("department_name") or "").strip()
        if not name:
            continue
        label = f"{name} — {department_name}" if department_name else name
        suffix = 2
        candidate = label
        while candidate in options:
            candidate = f"{label} ({suffix})"
            suffix += 1
        options[candidate] = str(row.get("id") or "").strip()
    return options


def _render_graph_tabs(
    *,
    title: str,
    html: str,
    frame: pd.DataFrame,
    fullscreen_key: str,
    table_fullscreen_key: str,
    caption: str,
    export_name: str,
    empty_graph_text: str,
) -> None:
    visual_tab, table_tab = st.tabs(["Візуалізація", "Таблиця та експорт"])

    with visual_tab:
        render_fullscreen_html_heading(
            title,
            html,
            key=fullscreen_key,
            height=980,
            caption=caption,
        )
        if html:
            components.html(html, height=760, scrolling=False)
        else:
            render_empty_state("Інтерактивний граф недоступний", empty_graph_text)

    with table_tab:
        if frame.empty:
            render_empty_state("Табличний зріз порожній", "Для поточного режиму поки що немає зв'язків для експорту.")
        else:
            render_fullscreen_dataframe_heading(
                "Табличний зріз графа",
                frame,
                key=table_fullscreen_key,
                caption="Повний список зв'язків для поточного режиму мережі.",
            )
            st.download_button(
                "Експорт поточного графа CSV",
                _csv_bytes(frame),
                file_name=export_name,
                mime="text/csv",
                use_container_width=True,
            )
            st.dataframe(frame, use_container_width=True, hide_index=True)


def render() -> None:
    service = require_service()
    render_header("Графова аналітика", subtitle="Перемикайте проєкції мережі між авторством, співавторством та міжкафедральними зв'язками.")

    mode = st.radio(
        "Режим мережі",
        ["Авторство", "Співавторство викладачів", "Профіль викладача", "Зв'язки між кафедрами"],
        horizontal=True,
    )
    controls = st.columns([1.15, 0.85], gap="large")
    edge_limit = controls[1].slider("Ліміт зв'язків", min_value=20, max_value=240, value=120, step=10)

    with st.expander("Як читати граф", expanded=False):
        if mode == "Авторство":
            st.caption("У цій проєкції вузли викладачів з'єднуються з вузлами публікацій. Це зручно для перевірки авторств і покриття записів.")
        elif mode == "Співавторство викладачів":
            st.caption("Тут показані прямі зв'язки між викладачами. Чим товстіше ребро, тим більше спільних робіт між парою.")
        elif mode == "Профіль викладача":
            st.caption("Цей режим будує локальну мережу навколо одного викладача: його публікації, найближчі співавтори та пов'язаний підрозділ.")
        else:
            st.caption("У цій проєкції видно співпрацю між кафедрами. Це один із найсильніших зрізів для демонстрації реальної мережевої взаємодії.")

    if mode == "Авторство":
        department_labels = _department_options(service)
        selected_department_label = controls[0].selectbox("Кафедра", list(department_labels.keys()))
        edges = service.get_graph_edges(department_code=department_labels[selected_department_label], limit=edge_limit)
        if not edges:
            render_empty_state("Недостатньо даних для графа", "Після завантаження публікацій тут з'явиться мережа авторства.")
            return

        teacher_count = len({edge["teacher_id"] for edge in edges})
        publication_count = len({edge["publication_id"] for edge in edges})
        summary = st.columns(3, gap="medium")
        summary[0].metric("Вузли викладачів", teacher_count)
        summary[1].metric("Вузли публікацій", publication_count)
        summary[2].metric("Зв'язки графа", len(edges))

        graph_html = build_bipartite_graph_html(edges)
        frame = graph_edges_dataframe(edges)
        _render_graph_tabs(
            title="Інтерактивна мережа авторства",
            html=graph_html,
            frame=frame,
            fullscreen_key="graph_bipartite_fullscreen",
            table_fullscreen_key="graph_bipartite_table_fullscreen",
            caption="Мережа авторства",
            export_name="graph_authorship_edges.csv",
            empty_graph_text="Бібліотека візуалізації не підключилася, тому використовуйте табличний зріз нижче.",
        )
        return

    if mode == "Співавторство викладачів":
        department_labels = _department_options(service)
        selected_department_label = controls[0].selectbox("Кафедра", list(department_labels.keys()))
        edges = service.get_teacher_coauthor_graph(
            department_code=department_labels[selected_department_label],
            limit=edge_limit,
        )
        if not edges:
            render_empty_state("Немає зв'язків співавторства", "Потрібні спільні публікації між викладачами, щоб побудувати цю проєкцію.")
            return

        teacher_count = len({edge["source_id"] for edge in edges} | {edge["target_id"] for edge in edges})
        total_weight = sum(int(edge.get("weight", 0) or 0) for edge in edges)
        summary = st.columns(3, gap="medium")
        summary[0].metric("Викладачі в мережі", teacher_count)
        summary[1].metric("Пари співавторів", len(edges))
        summary[2].metric("Сумарні спільні роботи", total_weight)

        graph_html = build_coauthor_graph_html(edges)
        frame = coauthor_graph_dataframe(edges)
        _render_graph_tabs(
            title="Інтерактивна мережа співавторства",
            html=graph_html,
            frame=frame,
            fullscreen_key="graph_coauthor_fullscreen",
            table_fullscreen_key="graph_coauthor_table_fullscreen",
            caption="Мережа співавторства викладачів",
            export_name="graph_coauthors.csv",
            empty_graph_text="Інтерактивна візуалізація недоступна, але табличний зріз зв'язків збережено.",
        )
        return

    if mode == "Профіль викладача":
        department_labels = _department_options(service)
        selected_department_label = controls[0].selectbox("Кафедра", list(department_labels.keys()))
        selected_department_code = department_labels[selected_department_label]
        teacher_rows = service.get_teachers()
        if selected_department_code:
            teacher_rows = [
                row for row in teacher_rows if str(row.get("department_code") or "").strip() == selected_department_code
            ]
        teacher_labels = _teacher_options(teacher_rows)
        if not teacher_labels:
            render_empty_state("Викладачі недоступні", "У вибраній кафедрі поки немає викладачів для побудови локального графа.")
            return

        selected_teacher_label = st.selectbox("Оберіть викладача", list(teacher_labels.keys()))
        selected_teacher_id = teacher_labels[selected_teacher_label]
        selected_teacher_profile = next(
            (row for row in teacher_rows if str(row.get("id") or "").strip() == selected_teacher_id),
            {},
        )
        edges = service.get_teacher_focus_graph(selected_teacher_id, limit=edge_limit)
        if not edges:
            render_empty_state("Локальний граф порожній", "Для цього викладача ще не знайдено публікацій або співавторських зв'язків.")
            return

        publication_count = len({edge["publication_id"] for edge in edges})
        teacher_count = len({edge["teacher_id"] for edge in edges})
        coauthor_count = max(teacher_count - 1, 0)
        summary = st.columns(3, gap="medium")
        summary[0].metric("Обраний викладач", edges[0].get("focus_teacher_name", selected_teacher_label))
        summary[1].metric("Публікації у фокусі", publication_count)
        summary[2].metric("Співавтори поруч", coauthor_count)

        render_key_value_card(
            "Профіль викладача",
            [
                ("ПІБ", str(selected_teacher_profile.get("full_name") or edges[0].get("focus_teacher_name") or "")),
                ("Кафедра", str(selected_teacher_profile.get("department_name") or "—")),
                ("Посада", str(selected_teacher_profile.get("position") or "—")),
                ("ORCID", str(selected_teacher_profile.get("orcid") or "—")),
                ("Scopus", str(selected_teacher_profile.get("scopus") or "—")),
                ("WoS", str(selected_teacher_profile.get("web_of_science") or "—")),
            ],
        )

        graph_html = build_bipartite_graph_html(edges, focus_teacher_id=selected_teacher_id)
        frame = graph_edges_dataframe(edges)
        _render_graph_tabs(
            title="Локальна мережа викладача",
            html=graph_html,
            frame=frame,
            fullscreen_key="graph_teacher_focus_fullscreen",
            table_fullscreen_key="graph_teacher_focus_table_fullscreen",
            caption="Публікації та співавтори навколо обраного викладача.",
            export_name="graph_teacher_focus.csv",
            empty_graph_text="Інтерактивна візуалізація недоступна, але нижче можна переглянути табличний зріз локального графа.",
        )
        return

    faculty_labels = _faculty_options(service)
    selected_faculty_label = controls[0].selectbox("Факультет", list(faculty_labels.keys()))
    edges = service.get_department_collaboration_edges(
        faculty_code=faculty_labels[selected_faculty_label],
        limit=edge_limit,
    )
    if not edges:
        render_empty_state("Міжкафедральних зв'язків поки немає", "Ця мережа з'явиться після накопичення спільних робіт між кафедрами.")
        return

    department_count = len({edge["source_id"] for edge in edges} | {edge["target_id"] for edge in edges})
    total_weight = sum(int(edge.get("weight", 0) or 0) for edge in edges)
    summary = st.columns(3, gap="medium")
    summary[0].metric("Кафедри в мережі", department_count)
    summary[1].metric("Міжкафедральні зв'язки", len(edges))
    summary[2].metric("Спільні роботи", total_weight)

    graph_html = build_department_graph_html(edges)
    frame = department_collaboration_dataframe(edges)
    _render_graph_tabs(
        title="Інтерактивна міжкафедральна мережа",
        html=graph_html,
        frame=frame,
        fullscreen_key="graph_department_fullscreen",
        table_fullscreen_key="graph_department_table_fullscreen",
        caption="Міжкафедральна мережа",
        export_name="graph_department_collaboration.csv",
        empty_graph_text="Інтерактивна візуалізація недоступна, але нижче доступний експорт поточного зрізу.",
    )
