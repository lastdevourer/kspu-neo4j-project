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
        "Академічна аналітика KSU",
        subtitle="Огляд структури університету, викладачів, публікацій і співавторства в одному просторі.",
    )

    counts = service.get_overview_counts()
    profile_coverage = service.get_profile_coverage()
    total_teachers = int(profile_coverage.get("teachers") or counts.get("teachers") or 0)
    publication_sources = publication_sources_dataframe(service.get_publication_source_summary())
    faculty_overview_rows = service.get_faculty_overview()
    department_overview_rows = service.get_department_overview()
    faculty_overview = faculty_overview_dataframe(faculty_overview_rows)
    department_overview = department_overview_dataframe(department_overview_rows)

    render_section_heading("Ключові показники", "Оперативний зріз структури, викладачів, публікацій і співавторства.")

    primary_columns = st.columns(4, gap="medium")
    primary_columns[0].metric("Викладачі", format_number(counts["teachers"]))
    primary_columns[1].metric("Публікації", format_number(counts["publications"]))
    primary_columns[2].metric("Авторства", format_number(counts["authorship_links"]))
    primary_columns[3].metric("Співавтори", format_number(counts["coauthor_pairs"]))

    secondary_columns = st.columns(2, gap="medium")
    secondary_columns[0].metric("Факультети", format_number(counts["faculties"]))
    secondary_columns[1].metric("Кафедри", format_number(counts["departments"]))

    if faculty_overview.empty and department_overview.empty:
        render_empty_state("Дані відсутні", "Завантажте викладачів KSU або відкрийте сторінку `Структура`, щоб заповнити базу.")
        return

    if counts["publications"] == 0:
        st.info("Структура вже заведена. Для наповнення бази відкрийте `Структура` і запустіть імпорт викладачів та публікацій.")
    else:
        st.success("База заповнена. Можна переходити до аналітики, графа та перегляду даних.")

    structure_tab, coverage_tab, distribution_tab = st.tabs(
        ["Структура зараз", "Покриття та джерела", "Розподіл і повний зріз"]
    )

    with structure_tab:
        overview_columns = st.columns([0.92, 1.08], gap="large")

        with overview_columns[0]:
            render_fullscreen_dataframe_heading(
                "Факультети",
                faculty_overview,
                key="dashboard_faculties_fullscreen",
                caption="Повна таблиця факультетів, кафедр, викладачів і публікацій.",
            )
            if faculty_overview.empty:
                render_empty_state("Немає даних", "Факультетний зріз з'явиться після імпорту структури.")
            else:
                st.download_button(
                    "Експорт факультетів CSV",
                    _csv_bytes(faculty_overview),
                    file_name="dashboard_faculties.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                _render_dashboard_table(faculty_overview)

        with overview_columns[1]:
            if department_overview.empty:
                render_section_heading("Кафедри")
                render_empty_state("Немає даних", "Таблиця кафедр з'явиться після імпорту структури.")
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
                    "Кафедри",
                    top_departments,
                    key="dashboard_departments_fullscreen",
                    caption="Поточний зріз кафедр за викладачами та публікаціями.",
                )
                st.download_button(
                    "Експорт кафедр CSV",
                    _csv_bytes(top_departments),
                    file_name="dashboard_departments.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                _render_dashboard_table(top_departments)

    with coverage_tab:
        render_section_heading("Покриття профілів і джерел")
        coverage_columns = st.columns(5, gap="medium")

        if total_teachers > 0:
            safe_total = max(total_teachers, 1)
            coverage_columns[0].metric("Будь-який профіль", f"{profile_coverage['with_any_profile']} / {safe_total}")
            coverage_columns[1].metric("ORCID", f"{profile_coverage['with_orcid']} / {safe_total}")
            coverage_columns[2].metric("Scholar", f"{profile_coverage['with_scholar']} / {safe_total}")
            coverage_columns[3].metric("Scopus", f"{profile_coverage['with_scopus']} / {safe_total}")
            coverage_columns[4].metric("WoS", f"{profile_coverage['with_wos']} / {safe_total}")

        source_columns = st.columns([1.05, 0.95], gap="large")
        with source_columns[0]:
            if publication_sources.empty:
                render_empty_state("Джерела ще не накопичені", "Після завантаження публікацій тут з'явиться зведення за сервісами.")
            else:
                chart_source = publication_sources.set_index("Джерело")
                render_fullscreen_bar_chart_heading(
                    "Структура джерел",
                    chart_source,
                    key="dashboard_sources_chart_fullscreen",
                )
                render_adaptive_bar_chart(chart_source, use_container_width=True, height=260)

        with source_columns[1]:
            if publication_sources.empty:
                render_empty_state("Таблиця джерел порожня", "Спершу потрібно імпортувати публікації.")
            else:
                render_fullscreen_dataframe_heading(
                    "Таблиця джерел",
                    publication_sources,
                    key="dashboard_sources_table_fullscreen",
                )
                render_adaptive_dataframe(publication_sources, use_container_width=True, hide_index=True, height=280)

    with distribution_tab:
        render_section_heading("Розподіл і повний зріз")
        full_columns = st.columns(2, gap="large")

        with full_columns[0]:
            render_fullscreen_dataframe_heading(
                "Повний список факультетів",
                faculty_overview,
                key="dashboard_faculties_fullscreen_full",
            )
            _render_dashboard_table(faculty_overview)

        with full_columns[1]:
            render_fullscreen_dataframe_heading(
                "Повний список кафедр",
                department_overview,
                key="dashboard_departments_fullscreen_full",
            )
            render_adaptive_dataframe(department_overview, use_container_width=True, hide_index=True, height=360)
