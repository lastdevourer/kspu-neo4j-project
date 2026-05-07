from __future__ import annotations

import streamlit as st

from ui.components import (
    render_adaptive_bar_chart,
    render_adaptive_dataframe,
    render_empty_state,
    render_fullscreen_bar_chart_heading,
    render_fullscreen_dataframe_heading,
    render_header,
    render_section_heading,
    require_service,
)
from ui.formatters import department_overview_dataframe, faculty_overview_dataframe, publication_sources_dataframe


def format_number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _csv_bytes(frame):
    return frame.to_csv(index=False).encode("utf-8-sig")


def _render_dashboard_table(frame) -> None:
    render_adaptive_dataframe(frame, use_container_width=True, hide_index=True, height=360)


def render() -> None:
    service = require_service()
    render_header(
        "ÐÐºÐ°Ð´ÐµÐ¼Ñ–Ñ‡Ð½Ð° Ð°Ð½Ð°Ð»Ñ–Ñ‚Ð¸ÐºÐ° KSU",
        subtitle="ÐžÐ³Ð»ÑÐ´ ÑÑ‚Ñ€ÑƒÐºÑ‚ÑƒÑ€Ð¸ ÑƒÐ½Ñ–Ð²ÐµÑ€ÑÐ¸Ñ‚ÐµÑ‚Ñƒ, Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð², Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹ Ñ– ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð° Ð² Ð¾Ð´Ð½Ð¾Ð¼Ñƒ Ð¿Ñ€Ð¾ÑÑ‚Ð¾Ñ€Ñ–.",
    )

    counts = service.get_overview_counts()
    profile_coverage = service.get_profile_coverage()
    total_teachers = int(profile_coverage.get("teachers") or counts.get("teachers") or 0)
    publication_sources = publication_sources_dataframe(service.get_publication_source_summary())
    faculty_overview_rows = service.get_faculty_overview()
    department_overview_rows = service.get_department_overview()
    faculty_overview = faculty_overview_dataframe(faculty_overview_rows)
    department_overview = department_overview_dataframe(department_overview_rows)

    render_section_heading("ÐšÐ»ÑŽÑ‡Ð¾Ð²Ñ– Ð¿Ð¾ÐºÐ°Ð·Ð½Ð¸ÐºÐ¸", "ÐžÐ¿ÐµÑ€Ð°Ñ‚Ð¸Ð²Ð½Ð¸Ð¹ Ð·Ñ€Ñ–Ð· ÑÑ‚Ñ€ÑƒÐºÑ‚ÑƒÑ€Ð¸, Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð², Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹ Ñ– ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð°.")

    primary_columns = st.columns(4, gap="medium")
    primary_columns[0].metric("Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–", format_number(counts["teachers"]))
    primary_columns[1].metric("ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—", format_number(counts["publications"]))
    primary_columns[2].metric("ÐÐ²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð°", format_number(counts["authorship_links"]))
    primary_columns[3].metric("Ð¡Ð¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€Ð¸", format_number(counts["coauthor_pairs"]))

    secondary_columns = st.columns(2, gap="medium")
    secondary_columns[0].metric("Ð¤Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚Ð¸", format_number(counts["faculties"]))
    secondary_columns[1].metric("ÐšÐ°Ñ„ÐµÐ´Ñ€Ð¸", format_number(counts["departments"]))

    if faculty_overview.empty and department_overview.empty:
        render_empty_state("Ð”Ð°Ð½Ñ– Ð²Ñ–Ð´ÑÑƒÑ‚Ð½Ñ–", "Ð—Ð°Ð²Ð°Ð½Ñ‚Ð°Ð¶Ñ‚Ðµ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð² KSU Ð°Ð±Ð¾ Ð²Ñ–Ð´ÐºÑ€Ð¸Ð¹Ñ‚Ðµ ÑÑ‚Ð¾Ñ€Ñ–Ð½ÐºÑƒ `Ð¡Ñ‚Ñ€ÑƒÐºÑ‚ÑƒÑ€Ð°`, Ñ‰Ð¾Ð± Ð·Ð°Ð¿Ð¾Ð²Ð½Ð¸Ñ‚Ð¸ Ð±Ð°Ð·Ñƒ.")
        return

    if counts["publications"] == 0:
        st.info("Ð¡Ñ‚Ñ€ÑƒÐºÑ‚ÑƒÑ€Ð° Ð²Ð¶Ðµ Ð·Ð°Ð²ÐµÐ´ÐµÐ½Ð°. Ð”Ð»Ñ Ð½Ð°Ð¿Ð¾Ð²Ð½ÐµÐ½Ð½Ñ Ð±Ð°Ð·Ð¸ Ð²Ñ–Ð´ÐºÑ€Ð¸Ð¹Ñ‚Ðµ `Ð¡Ñ‚Ñ€ÑƒÐºÑ‚ÑƒÑ€Ð°` Ñ– Ð·Ð°Ð¿ÑƒÑÑ‚Ñ–Ñ‚ÑŒ Ñ–Ð¼Ð¿Ð¾Ñ€Ñ‚ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð² Ñ‚Ð° Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹.")
    else:
        st.success("Ð‘Ð°Ð·Ð° Ð·Ð°Ð¿Ð¾Ð²Ð½ÐµÐ½Ð°. ÐœÐ¾Ð¶Ð½Ð° Ð¿ÐµÑ€ÐµÑ…Ð¾Ð´Ð¸Ñ‚Ð¸ Ð´Ð¾ Ð°Ð½Ð°Ð»Ñ–Ñ‚Ð¸ÐºÐ¸, Ð³Ñ€Ð°Ñ„Ð° Ñ‚Ð° Ð¿ÐµÑ€ÐµÐ³Ð»ÑÐ´Ñƒ Ð´Ð°Ð½Ð¸Ñ….")

    structure_tab, coverage_tab, distribution_tab = st.tabs(
        ["Ð¡Ñ‚Ñ€ÑƒÐºÑ‚ÑƒÑ€Ð° Ð·Ð°Ñ€Ð°Ð·", "ÐŸÐ¾ÐºÑ€Ð¸Ñ‚Ñ‚Ñ Ñ‚Ð° Ð´Ð¶ÐµÑ€ÐµÐ»Ð°", "Ð Ð¾Ð·Ð¿Ð¾Ð´Ñ–Ð» Ñ– Ð¿Ð¾Ð²Ð½Ð¸Ð¹ Ð·Ñ€Ñ–Ð·"]
    )

    with structure_tab:
        overview_columns = st.columns([0.92, 1.08], gap="large")

        with overview_columns[0]:
            render_fullscreen_dataframe_heading(
                "Ð¤Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚Ð¸",
                faculty_overview,
                key="dashboard_faculties_fullscreen",
                caption="ÐŸÐ¾Ð²Ð½Ð° Ñ‚Ð°Ð±Ð»Ð¸Ñ†Ñ Ñ„Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚Ñ–Ð², ÐºÐ°Ñ„ÐµÐ´Ñ€, Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð² Ñ– Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹.",
            )
            if faculty_overview.empty:
                render_empty_state("ÐÐµÐ¼Ð°Ñ” Ð´Ð°Ð½Ð¸Ñ…", "Ð¤Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚Ð½Ð¸Ð¹ Ð·Ñ€Ñ–Ð· Ð·'ÑÐ²Ð¸Ñ‚ÑŒÑÑ Ð¿Ñ–ÑÐ»Ñ Ñ–Ð¼Ð¿Ð¾Ñ€Ñ‚Ñƒ ÑÑ‚Ñ€ÑƒÐºÑ‚ÑƒÑ€Ð¸.")
            else:
                st.download_button(
                    "Ð•ÐºÑÐ¿Ð¾Ñ€Ñ‚ Ñ„Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚Ñ–Ð² CSV",
                    _csv_bytes(faculty_overview),
                    file_name="dashboard_faculties.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                _render_dashboard_table(faculty_overview)

        with overview_columns[1]:
            if department_overview.empty:
                render_section_heading("ÐšÐ°Ñ„ÐµÐ´Ñ€Ð¸")
                render_empty_state("ÐÐµÐ¼Ð°Ñ” Ð´Ð°Ð½Ð¸Ñ…", "Ð¢Ð°Ð±Ð»Ð¸Ñ†Ñ ÐºÐ°Ñ„ÐµÐ´Ñ€ Ð·'ÑÐ²Ð¸Ñ‚ÑŒÑÑ Ð¿Ñ–ÑÐ»Ñ Ñ–Ð¼Ð¿Ð¾Ñ€Ñ‚Ñƒ ÑÑ‚Ñ€ÑƒÐºÑ‚ÑƒÑ€Ð¸.")
            else:
                top_department_rows = sorted(
                    department_overview_rows,
                    key=lambda row: (
                        -(int(row.get("teachers") or 0)),
                        -(int(row.get("publications") or 0)),
                        str(row.get("name") or ""),
                    ),
                )[:8]
                top_departments = department_overview_dataframe(top_department_rows)
                render_fullscreen_dataframe_heading(
                    "ÐšÐ°Ñ„ÐµÐ´Ñ€Ð¸",
                    top_departments,
                    key="dashboard_departments_fullscreen",
                    caption="ÐŸÐ¾Ñ‚Ð¾Ñ‡Ð½Ð¸Ð¹ Ð·Ñ€Ñ–Ð· ÐºÐ°Ñ„ÐµÐ´Ñ€ Ð·Ð° Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°Ð¼Ð¸ Ñ‚Ð° Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑÐ¼Ð¸.",
                )
                st.download_button(
                    "Ð•ÐºÑÐ¿Ð¾Ñ€Ñ‚ ÐºÐ°Ñ„ÐµÐ´Ñ€ CSV",
                    _csv_bytes(top_departments),
                    file_name="dashboard_departments.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                _render_dashboard_table(top_departments)

    with coverage_tab:
        render_section_heading("ÐŸÐ¾ÐºÑ€Ð¸Ñ‚Ñ‚Ñ Ð¿Ñ€Ð¾Ñ„Ñ–Ð»Ñ–Ð² Ñ– Ð´Ð¶ÐµÑ€ÐµÐ»")
        coverage_columns = st.columns(5, gap="medium")

        if total_teachers > 0:
            safe_total = max(total_teachers, 1)
            coverage_columns[0].metric("Ð‘ÑƒÐ´ÑŒ-ÑÐºÐ¸Ð¹ Ð¿Ñ€Ð¾Ñ„Ñ–Ð»ÑŒ", f"{profile_coverage['with_any_profile']} / {safe_total}")
            coverage_columns[1].metric("ORCID", f"{profile_coverage['with_orcid']} / {safe_total}")
            coverage_columns[2].metric("Scholar", f"{profile_coverage['with_scholar']} / {safe_total}")
            coverage_columns[3].metric("Scopus", f"{profile_coverage['with_scopus']} / {safe_total}")
            coverage_columns[4].metric("WoS", f"{profile_coverage['with_wos']} / {safe_total}")

        source_columns = st.columns([1.05, 0.95], gap="large")
        with source_columns[0]:
            if publication_sources.empty:
                render_empty_state("Ð”Ð¶ÐµÑ€ÐµÐ»Ð° Ñ‰Ðµ Ð½Ðµ Ð½Ð°ÐºÐ¾Ð¿Ð¸Ñ‡ÐµÐ½Ñ–", "ÐŸÑ–ÑÐ»Ñ Ð·Ð°Ð²Ð°Ð½Ñ‚Ð°Ð¶ÐµÐ½Ð½Ñ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹ Ñ‚ÑƒÑ‚ Ð·'ÑÐ²Ð¸Ñ‚ÑŒÑÑ Ð·Ð²ÐµÐ´ÐµÐ½Ð½Ñ Ð·Ð° ÑÐµÑ€Ð²Ñ–ÑÐ°Ð¼Ð¸.")
            else:
                chart_source = publication_sources.set_index("Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾")
                render_fullscreen_bar_chart_heading(
                    "Ð¡Ñ‚Ñ€ÑƒÐºÑ‚ÑƒÑ€Ð° Ð´Ð¶ÐµÑ€ÐµÐ»",
                    chart_source,
                    key="dashboard_sources_chart_fullscreen",
                )
                render_adaptive_bar_chart(chart_source, use_container_width=True, height=260)

        with source_columns[1]:
            if publication_sources.empty:
                render_empty_state("Ð¢Ð°Ð±Ð»Ð¸Ñ†Ñ Ð´Ð¶ÐµÑ€ÐµÐ» Ð¿Ð¾Ñ€Ð¾Ð¶Ð½Ñ", "Ð¡Ð¿ÐµÑ€ÑˆÑƒ Ð¿Ð¾Ñ‚Ñ€Ñ–Ð±Ð½Ð¾ Ñ–Ð¼Ð¿Ð¾Ñ€Ñ‚ÑƒÐ²Ð°Ñ‚Ð¸ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—.")
            else:
                render_fullscreen_dataframe_heading(
                    "Ð¢Ð°Ð±Ð»Ð¸Ñ†Ñ Ð´Ð¶ÐµÑ€ÐµÐ»",
                    publication_sources,
                    key="dashboard_sources_table_fullscreen",
                )
                render_adaptive_dataframe(publication_sources, use_container_width=True, hide_index=True, height=280)

    with distribution_tab:
        render_section_heading("Ð Ð¾Ð·Ð¿Ð¾Ð´Ñ–Ð» Ñ– Ð¿Ð¾Ð²Ð½Ð¸Ð¹ Ð·Ñ€Ñ–Ð·")
        full_columns = st.columns(2, gap="large")

        with full_columns[0]:
            render_fullscreen_dataframe_heading(
                "ÐŸÐ¾Ð²Ð½Ð¸Ð¹ ÑÐ¿Ð¸ÑÐ¾Ðº Ñ„Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚Ñ–Ð²",
                faculty_overview,
                key="dashboard_faculties_fullscreen_full",
            )
            _render_dashboard_table(faculty_overview)

        with full_columns[1]:
            render_fullscreen_dataframe_heading(
                "ÐŸÐ¾Ð²Ð½Ð¸Ð¹ ÑÐ¿Ð¸ÑÐ¾Ðº ÐºÐ°Ñ„ÐµÐ´Ñ€",
                department_overview,
                key="dashboard_departments_fullscreen_full",
            )
            render_adaptive_dataframe(department_overview, use_container_width=True, hide_index=True, height=360)
