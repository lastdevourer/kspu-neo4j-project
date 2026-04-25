from __future__ import annotations

import streamlit as st

from ui.components import (
    render_empty_state,
    render_header,
    render_info_card,
    render_section_heading,
    render_summary_strip,
    require_service,
)
from ui.formatters import (
    centrality_dataframe,
    publication_sources_dataframe,
    top_coauthor_pairs_dataframe,
    top_teachers_dataframe,
)
from utils.analytics import build_diploma_summary, calculate_centrality_rows


def render() -> None:
    service = require_service()
    render_header("ÐÐ½Ð°Ð»Ñ–Ñ‚Ð¸ÐºÐ°", "")

    top_limit = st.slider("ÐšÑ–Ð»ÑŒÐºÑ–ÑÑ‚ÑŒ Ð·Ð°Ð¿Ð¸ÑÑ–Ð² Ñƒ Ñ‚Ð¾Ð¿Ð°Ñ…", min_value=5, max_value=20, value=10, step=1)

    top_teachers = service.get_top_teachers_by_publications(limit=top_limit)
    top_pairs = service.get_top_coauthor_pairs(limit=top_limit)
    centrality_rows = calculate_centrality_rows(service.get_coauthor_edges())[:top_limit]
    profile_coverage = service.get_profile_coverage()
    source_rows = publication_sources_dataframe(service.get_publication_source_summary())

    highlights = st.columns(3, gap="medium")
    with highlights[0]:
        render_summary_strip(
            "Ð›Ñ–Ð´ÐµÑ€ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹",
            top_teachers[0]["teacher"] if top_teachers else "â€”",
        )
    with highlights[1]:
        render_summary_strip(
            "ÐÐ°Ð¹ÑÐ¸Ð»ÑŒÐ½Ñ–ÑˆÐ° Ð¿Ð°Ñ€Ð°",
            f"{top_pairs[0]['teacher_a']} / {top_pairs[0]['teacher_b']}" if top_pairs else "â€”",
        )
    with highlights[2]:
        render_summary_strip(
            "Ð¦ÐµÐ½Ñ‚Ñ€Ð°Ð»ÑŒÐ½Ð¸Ð¹ Ð²ÑƒÐ·Ð¾Ð»",
            centrality_rows[0]["teacher"] if centrality_rows else "â€”",
        )

    render_section_heading("ÐŸÐ¾ÑÑÐ½ÐµÐ½Ð½Ñ Ð´Ð»Ñ Ð´Ð¸Ð¿Ð»Ð¾Ð¼Ð°")
    render_info_card(
        "ÐšÐ¾Ñ€Ð¾Ñ‚ÐºÐ¸Ð¹ Ð²Ð¸ÑÐ½Ð¾Ð²Ð¾Ðº",
        build_diploma_summary(top_teachers, top_pairs, centrality_rows),
    )

    if profile_coverage.get("teachers", 0):
        render_section_heading("Ð“Ð¾Ñ‚Ð¾Ð²Ð½Ñ–ÑÑ‚ÑŒ Ð¿Ñ€Ð¾Ñ„Ñ–Ð»Ñ–Ð² Ð´Ð¾ Ð°Ð²Ñ‚Ð¾Ð¼Ð°Ñ‚Ð¸Ñ‡Ð½Ð¾Ð³Ð¾ Ñ–Ð¼Ð¿Ð¾Ñ€Ñ‚Ñƒ")
        total_teachers = max(int(profile_coverage["teachers"] or 0), 1)
        readiness_columns = st.columns(4, gap="medium")
        readiness_columns[0].metric("ORCID", f"{profile_coverage['with_orcid']} / {total_teachers}")
        readiness_columns[1].metric("Scholar", f"{profile_coverage['with_scholar']} / {total_teachers}")
        readiness_columns[2].metric("Scopus", f"{profile_coverage['with_scopus']} / {total_teachers}")
        readiness_columns[3].metric("WoS", f"{profile_coverage['with_wos']} / {total_teachers}")

    top_columns = st.columns(2, gap="large")
    with top_columns[0]:
        render_section_heading("Ð¢Ð¾Ð¿ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð² Ð·Ð° ÐºÑ–Ð»ÑŒÐºÑ–ÑÑ‚ÑŽ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹")
        top_teachers_table = top_teachers_dataframe(top_teachers)
        if top_teachers_table.empty:
            render_empty_state(
                "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹Ð½Ñ– Ð´Ð°Ð½Ñ– Ð²Ñ–Ð´ÑÑƒÑ‚Ð½Ñ–",
                "ÐšÐ¾Ð»Ð¸ Ñƒ Ð±Ð°Ð·Ñ– Ð·'ÑÐ²Ð»ÑÑ‚ÑŒÑÑ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—, Ñ‚ÑƒÑ‚ Ð±ÑƒÐ´Ðµ ÑÑ„Ð¾Ñ€Ð¼Ð¾Ð²Ð°Ð½Ð¾ Ñ€ÐµÐ¹Ñ‚Ð¸Ð½Ð³ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð².",
            )
        else:
            st.dataframe(top_teachers_table, use_container_width=True, hide_index=True)

    with top_columns[1]:
        render_section_heading("Ð¢Ð¾Ð¿ Ð¿Ð°Ñ€ ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€Ñ–Ð²")
        top_pairs_table = top_coauthor_pairs_dataframe(top_pairs)
        if top_pairs_table.empty:
            render_empty_state(
                "ÐŸÐ°Ñ€Ð¸ ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€Ñ–Ð² Ð¿Ð¾ÐºÐ¸ Ð½Ðµ Ð²Ð¸ÑÐ²Ð»ÐµÐ½Ð¾",
                "ÐŸÑ–ÑÐ»Ñ Ð¿Ð¾ÑÐ²Ð¸ ÑÐ¿Ñ–Ð»ÑŒÐ½Ð¸Ñ… Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹ Ñ‚ÑƒÑ‚ Ð±ÑƒÐ´Ðµ Ð¿Ð¾ÐºÐ°Ð·Ð°Ð½Ð¾ ÑÑ‚Ñ–Ð¹ÐºÑ– Ð¿Ð°Ñ€Ð¸ ÐºÐ¾Ð»Ð°Ð±Ð¾Ñ€Ð°Ð½Ñ‚Ñ–Ð².",
            )
        else:
            st.dataframe(top_pairs_table, use_container_width=True, hide_index=True)

    render_section_heading("ÐœÐµÑ€ÐµÐ¶ÐµÐ²Ñ– Ð¿Ð¾ÐºÐ°Ð·Ð½Ð¸ÐºÐ¸")
    centrality_table = centrality_dataframe(centrality_rows)
    if centrality_table.empty:
        render_empty_state(
            "ÐÐµÐ´Ð¾ÑÑ‚Ð°Ñ‚Ð½ÑŒÐ¾ Ð´Ð°Ð½Ð¸Ñ… Ð´Ð»Ñ centrality",
            "Ð”Ð»Ñ Ñ€Ð¾Ð·Ñ€Ð°Ñ…ÑƒÐ½ÐºÑƒ degree centrality Ñ‚Ð° betweenness centrality Ð¿Ð¾Ñ‚Ñ€Ñ–Ð±Ð½Ñ– Ð·Ð²'ÑÐ·ÐºÐ¸ ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð° Ð¼Ñ–Ð¶ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°Ð¼Ð¸.",
        )
    else:
        st.dataframe(centrality_table, use_container_width=True, hide_index=True)

    render_section_heading("Ð¡Ñ‚Ñ€ÑƒÐºÑ‚ÑƒÑ€Ð° Ð´Ð¶ÐµÑ€ÐµÐ»")
    if source_rows.empty:
        render_empty_state(
            "Ð”Ð¶ÐµÑ€ÐµÐ»Ð° Ñ‰Ðµ Ð½Ðµ Ð½Ð°ÐºÐ¾Ð¿Ð¸Ñ‡ÐµÐ½Ñ–",
            "ÐŸÑ–ÑÐ»Ñ Ð·Ð°Ð²Ð°Ð½Ñ‚Ð°Ð¶ÐµÐ½Ð½Ñ Ñ€Ð¾Ð±Ñ–Ñ‚ Ñ‚ÑƒÑ‚ Ð±ÑƒÐ´Ðµ Ð²Ð¸Ð´Ð½Ð¾, ÑÐºÑ– ÑÐµÑ€Ð²Ñ–ÑÐ¸ Ñ€ÐµÐ°Ð»ÑŒÐ½Ð¾ Ð´Ð°ÑŽÑ‚ÑŒ Ð½Ð°Ð¹Ð±Ñ–Ð»ÑŒÑˆÐµ Ð¿Ð¾ÐºÑ€Ð¸Ñ‚Ñ‚Ñ.",
        )
    else:
        source_columns = st.columns([1.05, 0.95], gap="large")
        with source_columns[0]:
            st.bar_chart(source_rows.set_index("Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾"), use_container_width=True, height=280)
        with source_columns[1]:
            st.dataframe(source_rows, use_container_width=True, hide_index=True)
