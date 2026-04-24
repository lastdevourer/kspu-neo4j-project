from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from ui.components import render_empty_state, render_header, render_section_heading, require_service
from ui.formatters import graph_edges_dataframe
from utils.graph_visualization import build_graph_html


def render() -> None:
    service = require_service()
    render_header("Граф співавторства", "")

    departments = service.get_departments()
    department_labels = {"Усі кафедри": ""}
    for row in departments:
        department_labels[f"{row['name']} ({row['code']})"] = row["code"]

    controls = st.columns([1.15, 0.85], gap="large")
    selected_department_label = controls[0].selectbox("Кафедра", list(department_labels.keys()))
    edge_limit = controls[1].slider("Ліміт зв'язків", min_value=30, max_value=240, value=120, step=10)

    edges = service.get_graph_edges(
        department_code=department_labels[selected_department_label],
        limit=edge_limit,
    )

    if not edges:
        render_empty_state(
            "Недостатньо даних для графа",
            "Після завантаження публікацій тут з'явиться мережа співавторства.",
        )
        return

    teacher_count = len({edge["teacher_id"] for edge in edges})
    publication_count = len({edge["publication_id"] for edge in edges})
    summary_columns = st.columns(3, gap="medium")
    summary_columns[0].metric("Вузли викладачів", teacher_count)
    summary_columns[1].metric("Вузли публікацій", publication_count)
    summary_columns[2].metric("Зв'язки графа", len(edges))

    render_section_heading("Інтерактивна мережа")

    graph_html = build_graph_html(edges)
    if graph_html:
        components.html(graph_html, height=760, scrolling=False)
    else:
        render_empty_state(
            "Інтерактивний граф недоступний",
            "Бібліотека візуалізації не підключилася, тому нижче показано табличне представлення зв'язків авторства."
        )
        st.dataframe(graph_edges_dataframe(edges), use_container_width=True, hide_index=True)

    with st.expander("Показати таблицю зв'язків", expanded=False):
        st.dataframe(graph_edges_dataframe(edges), use_container_width=True, hide_index=True)
