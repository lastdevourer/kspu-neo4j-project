from __future__ import annotations

import streamlit as st

from ui.components import render_empty_state, render_header, render_section_heading, render_summary_strip, require_service
from ui.formatters import department_overview_dataframe


def format_number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def render() -> None:
    service = require_service()
    render_header(
        "Аналітика наукових публікацій викладачів",
        "Факультети, кафедри, викладачі та мережеві зв'язки в одному просторі.",
    )

    counts = service.get_overview_counts()
    department_overview = department_overview_dataframe(service.get_department_overview())

    render_section_heading("Ключові показники")

    primary_columns = st.columns(4, gap="medium")
    primary_columns[0].metric("Викладачі", format_number(counts["teachers"]))
    primary_columns[1].metric("Публікації", format_number(counts["publications"]))
    primary_columns[2].metric("Зв'язки авторства", format_number(counts["authorship_links"]))
    primary_columns[3].metric("Пари співавторів", format_number(counts["coauthor_pairs"]))

    secondary_columns = st.columns(2, gap="medium")
    secondary_columns[0].metric("Факультети", format_number(counts["faculties"]))
    secondary_columns[1].metric("Кафедри", format_number(counts["departments"]))

    if counts["teachers"] == 0 and counts["publications"] == 0:
        render_empty_state(
            "База ще не заповнена",
            "Структура факультетів і кафедр уже готова. Наступний крок — імпорт викладачів, профілів та публікацій.",
        )

    left, right = st.columns([0.9, 1.3], gap="large")

    with left:
        render_section_heading("Наповнення бази")
        render_summary_strip(
            "Довідник структури",
            f"{counts['faculties']} факультетів / {counts['departments']} кафедр",
            "Офіційний контур підрозділів підготовлено для подальшого імпорту викладачів.",
        )
        render_summary_strip(
            "Наступний етап",
            "Імпорт викладачів",
            "Збираємо кадровий склад кафедр, посади та профільні посилання на ORCID, Google Scholar, Scopus.",
        )
        render_summary_strip(
            "Для сильного MVP",
            "2-3 кафедри з публікаціями",
            "Цього вже достатньо, щоб граф співавторства, рейтинги та centrality виглядали переконливо на захисті.",
        )

        render_section_heading("Факультетний зріз")
        if department_overview.empty:
            render_empty_state(
                "Ще немає структурного зрізу",
                "Після заповнення довідника тут з'явиться короткий огляд факультетів і кафедр.",
            )
        else:
            faculty_overview = (
                department_overview.groupby("Факультет", as_index=False)
                .agg({"Кафедра": "count", "Викладачі": "sum", "Публікації": "sum"})
                .rename(columns={"Кафедра": "Кафедри"})
                .sort_values(by=["Кафедри", "Факультет"], ascending=[False, True])
            )
            st.dataframe(faculty_overview, use_container_width=True, hide_index=True)

    with right:
        render_section_heading("Структура факультетів і кафедр")
        if department_overview.empty:
            render_empty_state(
                "Немає довідкових даних",
                "Після заповнення факультетів і кафедр тут з'явиться структурована таблиця підрозділів.",
            )
        else:
            st.dataframe(department_overview, use_container_width=True, hide_index=True)
