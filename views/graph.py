from __future__ import annotations

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from config import get_ui_theme
from ui.components import (
    render_empty_state,
    render_adaptive_dataframe,
    render_fullscreen_dataframe_heading,
    render_fullscreen_html_heading,
    render_header,
    render_key_value_card,
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
    options = {"Ð£ÑÑ– ÐºÐ°Ñ„ÐµÐ´Ñ€Ð¸": ""}
    for row in rows:
        faculty_name = str(row.get("faculty_name") or "").strip()
        label = f"{row['name']} â€” {faculty_name}" if faculty_name else str(row["name"])
        options[label] = row["code"]
    return options


def _faculty_options(service) -> dict[str, str]:
    rows = service.get_faculty_overview()
    options = {"Ð£ÑÑ– Ñ„Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚Ð¸": ""}
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
        label = f"{name} â€” {department_name}" if department_name else name
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
    visual_tab, table_tab = st.tabs(["Ð’Ñ–Ð·ÑƒÐ°Ð»Ñ–Ð·Ð°Ñ†Ñ–Ñ", "Ð¢Ð°Ð±Ð»Ð¸Ñ†Ñ Ñ‚Ð° ÐµÐºÑÐ¿Ð¾Ñ€Ñ‚"])

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
            render_empty_state("Ð†Ð½Ñ‚ÐµÑ€Ð°ÐºÑ‚Ð¸Ð²Ð½Ð¸Ð¹ Ð³Ñ€Ð°Ñ„ Ð½ÐµÐ´Ð¾ÑÑ‚ÑƒÐ¿Ð½Ð¸Ð¹", empty_graph_text)

    with table_tab:
        if frame.empty:
            render_empty_state("Ð¢Ð°Ð±Ð»Ð¸Ñ‡Ð½Ð¸Ð¹ Ð·Ñ€Ñ–Ð· Ð¿Ð¾Ñ€Ð¾Ð¶Ð½Ñ–Ð¹", "Ð”Ð»Ñ Ð¿Ð¾Ñ‚Ð¾Ñ‡Ð½Ð¾Ð³Ð¾ Ñ€ÐµÐ¶Ð¸Ð¼Ñƒ Ð¿Ð¾ÐºÐ¸ Ñ‰Ð¾ Ð½ÐµÐ¼Ð°Ñ” Ð·Ð²'ÑÐ·ÐºÑ–Ð² Ð´Ð»Ñ ÐµÐºÑÐ¿Ð¾Ñ€Ñ‚Ñƒ.")
        else:
            render_fullscreen_dataframe_heading(
                "Ð¢Ð°Ð±Ð»Ð¸Ñ‡Ð½Ð¸Ð¹ Ð·Ñ€Ñ–Ð· Ð³Ñ€Ð°Ñ„Ð°",
                frame,
                key=table_fullscreen_key,
                caption="ÐŸÐ¾Ð²Ð½Ð¸Ð¹ ÑÐ¿Ð¸ÑÐ¾Ðº Ð·Ð²'ÑÐ·ÐºÑ–Ð² Ð´Ð»Ñ Ð¿Ð¾Ñ‚Ð¾Ñ‡Ð½Ð¾Ð³Ð¾ Ñ€ÐµÐ¶Ð¸Ð¼Ñƒ Ð¼ÐµÑ€ÐµÐ¶Ñ–.",
            )
            st.download_button(
                "Ð•ÐºÑÐ¿Ð¾Ñ€Ñ‚ Ð¿Ð¾Ñ‚Ð¾Ñ‡Ð½Ð¾Ð³Ð¾ Ð³Ñ€Ð°Ñ„Ð° CSV",
                _csv_bytes(frame),
                file_name=export_name,
                mime="text/csv",
                use_container_width=True,
            )
            render_adaptive_dataframe(frame, use_container_width=True, hide_index=True, height=420)


def render() -> None:
    service = require_service()
    ui_theme = get_ui_theme()
    render_header(
        "ÐœÐµÑ€ÐµÐ¶ÐµÐ²Ð° Ð°Ð½Ð°Ð»Ñ–Ñ‚Ð¸ÐºÐ°",
        subtitle="Ð”Ð¾ÑÐ»Ñ–Ð´Ð¶ÑƒÐ¹Ñ‚Ðµ Ð·Ð²'ÑÐ·ÐºÐ¸ Ð¼Ñ–Ð¶ Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð¾Ð¼, ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð¾Ð¼, ÐºÐ°Ñ„ÐµÐ´Ñ€Ð°Ð¼Ð¸ Ñ‚Ð° Ð¾ÐºÑ€ÐµÐ¼Ð¸Ð¼Ð¸ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°Ð¼Ð¸.",
    )
    mode_options = ["ÐÐ²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð¾", "Ð¡Ð¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð¾ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð²", "ÐŸÑ€Ð¾Ñ„Ñ–Ð»ÑŒ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°", "Ð—'ÑÐ·ÐºÐ¸ Ð¼Ñ–Ð¶ ÐºÐ°Ñ„ÐµÐ´Ñ€Ð°Ð¼Ð¸"]
    mode = st.selectbox("Ð¢Ð¸Ð¿ Ð¼ÐµÑ€ÐµÐ¶Ñ–", mode_options, index=0, help="ÐžÐ±ÐµÑ€Ñ–Ñ‚ÑŒ Ð¿Ñ€Ð¾Ñ”ÐºÑ†Ñ–ÑŽ Ð³Ñ€Ð°Ñ„Ð° Ð´Ð»Ñ Ð¿Ð¾Ñ‚Ð¾Ñ‡Ð½Ð¾Ð³Ð¾ Ð°Ð½Ð°Ð»Ñ–Ð·Ñƒ.")
    controls = st.columns([1.15, 0.85], gap="large")
    edge_limit = controls[1].slider("Ð›Ñ–Ð¼Ñ–Ñ‚ Ð·Ð²'ÑÐ·ÐºÑ–Ð²", min_value=20, max_value=240, value=120, step=10)

    with st.expander("Ð¯Ðº Ñ‡Ð¸Ñ‚Ð°Ñ‚Ð¸ Ð³Ñ€Ð°Ñ„", expanded=False):
        if mode == "ÐÐ²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð¾":
            st.caption("Ð£ Ñ†Ñ–Ð¹ Ð¿Ñ€Ð¾Ñ”ÐºÑ†Ñ–Ñ— Ð²ÑƒÐ·Ð»Ð¸ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð² Ð·'Ñ”Ð´Ð½ÑƒÑŽÑ‚ÑŒÑÑ Ð· Ð²ÑƒÐ·Ð»Ð°Ð¼Ð¸ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹. Ð¦Ðµ Ð·Ñ€ÑƒÑ‡Ð½Ð¾ Ð´Ð»Ñ Ð¿ÐµÑ€ÐµÐ²Ñ–Ñ€ÐºÐ¸ Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð² Ñ– Ð¿Ð¾ÐºÑ€Ð¸Ñ‚Ñ‚Ñ Ð·Ð°Ð¿Ð¸ÑÑ–Ð².")
        elif mode == "Ð¡Ð¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð¾ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð²":
            st.caption("Ð¢ÑƒÑ‚ Ð¿Ð¾ÐºÐ°Ð·Ð°Ð½Ñ– Ð¿Ñ€ÑÐ¼Ñ– Ð·Ð²'ÑÐ·ÐºÐ¸ Ð¼Ñ–Ð¶ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°Ð¼Ð¸. Ð§Ð¸Ð¼ Ñ‚Ð¾Ð²ÑÑ‚Ñ–ÑˆÐµ Ñ€ÐµÐ±Ñ€Ð¾, Ñ‚Ð¸Ð¼ Ð±Ñ–Ð»ÑŒÑˆÐµ ÑÐ¿Ñ–Ð»ÑŒÐ½Ð¸Ñ… Ñ€Ð¾Ð±Ñ–Ñ‚ Ð¼Ñ–Ð¶ Ð¿Ð°Ñ€Ð¾ÑŽ.")
        elif mode == "ÐŸÑ€Ð¾Ñ„Ñ–Ð»ÑŒ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°":
            st.caption("Ð¦ÐµÐ¹ Ñ€ÐµÐ¶Ð¸Ð¼ Ð±ÑƒÐ´ÑƒÑ” Ð»Ð¾ÐºÐ°Ð»ÑŒÐ½Ñƒ Ð¼ÐµÑ€ÐµÐ¶Ñƒ Ð½Ð°Ð²ÐºÐ¾Ð»Ð¾ Ð¾Ð´Ð½Ð¾Ð³Ð¾ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°: Ð¹Ð¾Ð³Ð¾ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—, Ð½Ð°Ð¹Ð±Ð»Ð¸Ð¶Ñ‡Ñ– ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€Ð¸ Ñ‚Ð° Ð¿Ð¾Ð²'ÑÐ·Ð°Ð½Ð¸Ð¹ Ð¿Ñ–Ð´Ñ€Ð¾Ð·Ð´Ñ–Ð».")
        else:
            st.caption("Ð£ Ñ†Ñ–Ð¹ Ð¿Ñ€Ð¾Ñ”ÐºÑ†Ñ–Ñ— Ð²Ð¸Ð´Ð½Ð¾ ÑÐ¿Ñ–Ð²Ð¿Ñ€Ð°Ñ†ÑŽ Ð¼Ñ–Ð¶ ÐºÐ°Ñ„ÐµÐ´Ñ€Ð°Ð¼Ð¸. Ð¦Ðµ Ð¾Ð´Ð¸Ð½ Ñ–Ð· Ð½Ð°Ð¹ÑÐ¸Ð»ÑŒÐ½Ñ–ÑˆÐ¸Ñ… Ð·Ñ€Ñ–Ð·Ñ–Ð² Ð´Ð»Ñ Ð´ÐµÐ¼Ð¾Ð½ÑÑ‚Ñ€Ð°Ñ†Ñ–Ñ— Ñ€ÐµÐ°Ð»ÑŒÐ½Ð¾Ñ— Ð¼ÐµÑ€ÐµÐ¶ÐµÐ²Ð¾Ñ— Ð²Ð·Ð°Ñ”Ð¼Ð¾Ð´Ñ–Ñ—.")

    if mode == "ÐÐ²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð¾":
        department_labels = _department_options(service)
        selected_department_label = controls[0].selectbox("ÐšÐ°Ñ„ÐµÐ´Ñ€Ð°", list(department_labels.keys()))
        edges = service.get_graph_edges(department_code=department_labels[selected_department_label], limit=edge_limit)
        if not edges:
            render_empty_state("ÐÐµÐ´Ð¾ÑÑ‚Ð°Ñ‚Ð½ÑŒÐ¾ Ð´Ð°Ð½Ð¸Ñ… Ð´Ð»Ñ Ð³Ñ€Ð°Ñ„Ð°", "ÐŸÑ–ÑÐ»Ñ Ð·Ð°Ð²Ð°Ð½Ñ‚Ð°Ð¶ÐµÐ½Ð½Ñ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹ Ñ‚ÑƒÑ‚ Ð·'ÑÐ²Ð¸Ñ‚ÑŒÑÑ Ð¼ÐµÑ€ÐµÐ¶Ð° Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð°.")
            return

        teacher_count = len({edge["teacher_id"] for edge in edges})
        publication_count = len({edge["publication_id"] for edge in edges})
        summary = st.columns(3, gap="medium")
        summary[0].metric("Ð’ÑƒÐ·Ð»Ð¸ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð²", teacher_count)
        summary[1].metric("Ð’ÑƒÐ·Ð»Ð¸ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹", publication_count)
        summary[2].metric("Ð—Ð²'ÑÐ·ÐºÐ¸ Ð³Ñ€Ð°Ñ„Ð°", len(edges))

        graph_html = build_bipartite_graph_html(edges, theme=ui_theme)
        frame = graph_edges_dataframe(edges)
        _render_graph_tabs(
            title="Ð†Ð½Ñ‚ÐµÑ€Ð°ÐºÑ‚Ð¸Ð²Ð½Ð° Ð¼ÐµÑ€ÐµÐ¶Ð° Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð°",
            html=graph_html,
            frame=frame,
            fullscreen_key="graph_bipartite_fullscreen",
            table_fullscreen_key="graph_bipartite_table_fullscreen",
            caption="ÐœÐµÑ€ÐµÐ¶Ð° Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð°",
            export_name="graph_authorship_edges.csv",
            empty_graph_text="Ð‘Ñ–Ð±Ð»Ñ–Ð¾Ñ‚ÐµÐºÐ° Ð²Ñ–Ð·ÑƒÐ°Ð»Ñ–Ð·Ð°Ñ†Ñ–Ñ— Ð½Ðµ Ð¿Ñ–Ð´ÐºÐ»ÑŽÑ‡Ð¸Ð»Ð°ÑÑ, Ñ‚Ð¾Ð¼Ñƒ Ð²Ð¸ÐºÐ¾Ñ€Ð¸ÑÑ‚Ð¾Ð²ÑƒÐ¹Ñ‚Ðµ Ñ‚Ð°Ð±Ð»Ð¸Ñ‡Ð½Ð¸Ð¹ Ð·Ñ€Ñ–Ð· Ð½Ð¸Ð¶Ñ‡Ðµ.",
        )
        return

    if mode == "Ð¡Ð¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð¾ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð²":
        department_labels = _department_options(service)
        selected_department_label = controls[0].selectbox("ÐšÐ°Ñ„ÐµÐ´Ñ€Ð°", list(department_labels.keys()))
        edges = service.get_teacher_coauthor_graph(
            department_code=department_labels[selected_department_label],
            limit=edge_limit,
        )
        if not edges:
            render_empty_state("ÐÐµÐ¼Ð°Ñ” Ð·Ð²'ÑÐ·ÐºÑ–Ð² ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð°", "ÐŸÐ¾Ñ‚Ñ€Ñ–Ð±Ð½Ñ– ÑÐ¿Ñ–Ð»ÑŒÐ½Ñ– Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ð¼Ñ–Ð¶ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°Ð¼Ð¸, Ñ‰Ð¾Ð± Ð¿Ð¾Ð±ÑƒÐ´ÑƒÐ²Ð°Ñ‚Ð¸ Ñ†ÑŽ Ð¿Ñ€Ð¾Ñ”ÐºÑ†Ñ–ÑŽ.")
            return

        teacher_count = len({edge["source_id"] for edge in edges} | {edge["target_id"] for edge in edges})
        total_weight = sum(int(edge.get("weight", 0) or 0) for edge in edges)
        summary = st.columns(3, gap="medium")
        summary[0].metric("Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ– Ð² Ð¼ÐµÑ€ÐµÐ¶Ñ–", teacher_count)
        summary[1].metric("ÐŸÐ°Ñ€Ð¸ ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€Ñ–Ð²", len(edges))
        summary[2].metric("Ð¡ÑƒÐ¼Ð°Ñ€Ð½Ñ– ÑÐ¿Ñ–Ð»ÑŒÐ½Ñ– Ñ€Ð¾Ð±Ð¾Ñ‚Ð¸", total_weight)

        graph_html = build_coauthor_graph_html(edges, theme=ui_theme)
        frame = coauthor_graph_dataframe(edges)
        _render_graph_tabs(
            title="Ð†Ð½Ñ‚ÐµÑ€Ð°ÐºÑ‚Ð¸Ð²Ð½Ð° Ð¼ÐµÑ€ÐµÐ¶Ð° ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð°",
            html=graph_html,
            frame=frame,
            fullscreen_key="graph_coauthor_fullscreen",
            table_fullscreen_key="graph_coauthor_table_fullscreen",
            caption="ÐœÐµÑ€ÐµÐ¶Ð° ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð° Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð²",
            export_name="graph_coauthors.csv",
            empty_graph_text="Ð†Ð½Ñ‚ÐµÑ€Ð°ÐºÑ‚Ð¸Ð²Ð½Ð° Ð²Ñ–Ð·ÑƒÐ°Ð»Ñ–Ð·Ð°Ñ†Ñ–Ñ Ð½ÐµÐ´Ð¾ÑÑ‚ÑƒÐ¿Ð½Ð°, Ð°Ð»Ðµ Ñ‚Ð°Ð±Ð»Ð¸Ñ‡Ð½Ð¸Ð¹ Ð·Ñ€Ñ–Ð· Ð·Ð²'ÑÐ·ÐºÑ–Ð² Ð·Ð±ÐµÑ€ÐµÐ¶ÐµÐ½Ð¾.",
        )
        return

    if mode == "ÐŸÑ€Ð¾Ñ„Ñ–Ð»ÑŒ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°":
        department_labels = _department_options(service)
        selected_department_label = controls[0].selectbox("ÐšÐ°Ñ„ÐµÐ´Ñ€Ð°", list(department_labels.keys()))
        selected_department_code = department_labels[selected_department_label]
        teacher_rows = service.get_teachers()
        if selected_department_code:
            teacher_rows = [
                row for row in teacher_rows if str(row.get("department_code") or "").strip() == selected_department_code
            ]
        teacher_labels = _teacher_options(teacher_rows)
        if not teacher_labels:
            render_empty_state("Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ– Ð½ÐµÐ´Ð¾ÑÑ‚ÑƒÐ¿Ð½Ñ–", "Ð£ Ð²Ð¸Ð±Ñ€Ð°Ð½Ñ–Ð¹ ÐºÐ°Ñ„ÐµÐ´Ñ€Ñ– Ð¿Ð¾ÐºÐ¸ Ð½ÐµÐ¼Ð°Ñ” Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð² Ð´Ð»Ñ Ð¿Ð¾Ð±ÑƒÐ´Ð¾Ð²Ð¸ Ð»Ð¾ÐºÐ°Ð»ÑŒÐ½Ð¾Ð³Ð¾ Ð³Ñ€Ð°Ñ„Ð°.")
            return

        selected_teacher_label = st.selectbox("ÐžÐ±ÐµÑ€Ñ–Ñ‚ÑŒ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°", list(teacher_labels.keys()))
        selected_teacher_id = teacher_labels[selected_teacher_label]
        selected_teacher_profile = next(
            (row for row in teacher_rows if str(row.get("id") or "").strip() == selected_teacher_id),
            {},
        )
        edges = service.get_teacher_focus_graph(selected_teacher_id, limit=edge_limit)
        if not edges:
            render_empty_state("Ð›Ð¾ÐºÐ°Ð»ÑŒÐ½Ð¸Ð¹ Ð³Ñ€Ð°Ñ„ Ð¿Ð¾Ñ€Ð¾Ð¶Ð½Ñ–Ð¹", "Ð”Ð»Ñ Ñ†ÑŒÐ¾Ð³Ð¾ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð° Ñ‰Ðµ Ð½Ðµ Ð·Ð½Ð°Ð¹Ð´ÐµÐ½Ð¾ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹ Ð°Ð±Ð¾ ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€ÑÑŒÐºÐ¸Ñ… Ð·Ð²'ÑÐ·ÐºÑ–Ð².")
            return

        publication_count = len({edge["publication_id"] for edge in edges})
        teacher_count = len({edge["teacher_id"] for edge in edges})
        coauthor_count = max(teacher_count - 1, 0)
        summary = st.columns(3, gap="medium")
        summary[0].metric("ÐžÐ±Ñ€Ð°Ð½Ð¸Ð¹ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡", edges[0].get("focus_teacher_name", selected_teacher_label))
        summary[1].metric("ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ñƒ Ñ„Ð¾ÐºÑƒÑÑ–", publication_count)
        summary[2].metric("Ð¡Ð¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€Ð¸ Ð¿Ð¾Ñ€ÑƒÑ‡", coauthor_count)

        render_key_value_card(
            "ÐŸÑ€Ð¾Ñ„Ñ–Ð»ÑŒ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°",
            [
                ("ÐŸÐ†Ð‘", str(selected_teacher_profile.get("full_name") or edges[0].get("focus_teacher_name") or "")),
                ("ÐšÐ°Ñ„ÐµÐ´Ñ€Ð°", str(selected_teacher_profile.get("department_name") or "â€”")),
                ("ÐŸÐ¾ÑÐ°Ð´Ð°", str(selected_teacher_profile.get("position") or "â€”")),
                ("ORCID", str(selected_teacher_profile.get("orcid") or "â€”")),
                ("Scopus", str(selected_teacher_profile.get("scopus") or "â€”")),
                ("WoS", str(selected_teacher_profile.get("web_of_science") or "â€”")),
            ],
        )

        graph_html = build_bipartite_graph_html(edges, focus_teacher_id=selected_teacher_id, theme=ui_theme)
        frame = graph_edges_dataframe(edges)
        _render_graph_tabs(
            title="Ð›Ð¾ÐºÐ°Ð»ÑŒÐ½Ð° Ð¼ÐµÑ€ÐµÐ¶Ð° Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°",
            html=graph_html,
            frame=frame,
            fullscreen_key="graph_teacher_focus_fullscreen",
            table_fullscreen_key="graph_teacher_focus_table_fullscreen",
            caption="ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ñ‚Ð° ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€Ð¸ Ð½Ð°Ð²ÐºÐ¾Ð»Ð¾ Ð¾Ð±Ñ€Ð°Ð½Ð¾Ð³Ð¾ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°.",
            export_name="graph_teacher_focus.csv",
            empty_graph_text="Ð†Ð½Ñ‚ÐµÑ€Ð°ÐºÑ‚Ð¸Ð²Ð½Ð° Ð²Ñ–Ð·ÑƒÐ°Ð»Ñ–Ð·Ð°Ñ†Ñ–Ñ Ð½ÐµÐ´Ð¾ÑÑ‚ÑƒÐ¿Ð½Ð°, Ð°Ð»Ðµ Ð½Ð¸Ð¶Ñ‡Ðµ Ð¼Ð¾Ð¶Ð½Ð° Ð¿ÐµÑ€ÐµÐ³Ð»ÑÐ½ÑƒÑ‚Ð¸ Ñ‚Ð°Ð±Ð»Ð¸Ñ‡Ð½Ð¸Ð¹ Ð·Ñ€Ñ–Ð· Ð»Ð¾ÐºÐ°Ð»ÑŒÐ½Ð¾Ð³Ð¾ Ð³Ñ€Ð°Ñ„Ð°.",
        )
        return

    faculty_labels = _faculty_options(service)
    selected_faculty_label = controls[0].selectbox("Ð¤Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚", list(faculty_labels.keys()))
    edges = service.get_department_collaboration_edges(
        faculty_code=faculty_labels[selected_faculty_label],
        limit=edge_limit,
    )
    if not edges:
        render_empty_state("ÐœÑ–Ð¶ÐºÐ°Ñ„ÐµÐ´Ñ€Ð°Ð»ÑŒÐ½Ð¸Ñ… Ð·Ð²'ÑÐ·ÐºÑ–Ð² Ð¿Ð¾ÐºÐ¸ Ð½ÐµÐ¼Ð°Ñ”", "Ð¦Ñ Ð¼ÐµÑ€ÐµÐ¶Ð° Ð·'ÑÐ²Ð¸Ñ‚ÑŒÑÑ Ð¿Ñ–ÑÐ»Ñ Ð½Ð°ÐºÐ¾Ð¿Ð¸Ñ‡ÐµÐ½Ð½Ñ ÑÐ¿Ñ–Ð»ÑŒÐ½Ð¸Ñ… Ñ€Ð¾Ð±Ñ–Ñ‚ Ð¼Ñ–Ð¶ ÐºÐ°Ñ„ÐµÐ´Ñ€Ð°Ð¼Ð¸.")
        return

    department_count = len({edge["source_id"] for edge in edges} | {edge["target_id"] for edge in edges})
    total_weight = sum(int(edge.get("weight", 0) or 0) for edge in edges)
    summary = st.columns(3, gap="medium")
    summary[0].metric("ÐšÐ°Ñ„ÐµÐ´Ñ€Ð¸ Ð² Ð¼ÐµÑ€ÐµÐ¶Ñ–", department_count)
    summary[1].metric("ÐœÑ–Ð¶ÐºÐ°Ñ„ÐµÐ´Ñ€Ð°Ð»ÑŒÐ½Ñ– Ð·Ð²'ÑÐ·ÐºÐ¸", len(edges))
    summary[2].metric("Ð¡Ð¿Ñ–Ð»ÑŒÐ½Ñ– Ñ€Ð¾Ð±Ð¾Ñ‚Ð¸", total_weight)

    graph_html = build_department_graph_html(edges, theme=ui_theme)
    frame = department_collaboration_dataframe(edges)
    _render_graph_tabs(
        title="Ð†Ð½Ñ‚ÐµÑ€Ð°ÐºÑ‚Ð¸Ð²Ð½Ð° Ð¼Ñ–Ð¶ÐºÐ°Ñ„ÐµÐ´Ñ€Ð°Ð»ÑŒÐ½Ð° Ð¼ÐµÑ€ÐµÐ¶Ð°",
        html=graph_html,
        frame=frame,
        fullscreen_key="graph_department_fullscreen",
        table_fullscreen_key="graph_department_table_fullscreen",
        caption="ÐœÑ–Ð¶ÐºÐ°Ñ„ÐµÐ´Ñ€Ð°Ð»ÑŒÐ½Ð° Ð¼ÐµÑ€ÐµÐ¶Ð°",
        export_name="graph_department_collaboration.csv",
        empty_graph_text="Ð†Ð½Ñ‚ÐµÑ€Ð°ÐºÑ‚Ð¸Ð²Ð½Ð° Ð²Ñ–Ð·ÑƒÐ°Ð»Ñ–Ð·Ð°Ñ†Ñ–Ñ Ð½ÐµÐ´Ð¾ÑÑ‚ÑƒÐ¿Ð½Ð°, Ð°Ð»Ðµ Ð½Ð¸Ð¶Ñ‡Ðµ Ð´Ð¾ÑÑ‚ÑƒÐ¿Ð½Ð¸Ð¹ ÐµÐºÑÐ¿Ð¾Ñ€Ñ‚ Ð¿Ð¾Ñ‚Ð¾Ñ‡Ð½Ð¾Ð³Ð¾ Ð·Ñ€Ñ–Ð·Ñƒ.",
    )
