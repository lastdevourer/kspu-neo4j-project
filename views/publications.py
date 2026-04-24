from __future__ import annotations

import streamlit as st

from ui.components import (
    render_empty_state,
    render_header,
    render_key_value_card,
    render_section_heading,
    render_summary_strip,
    require_service,
)
from ui.formatters import publications_dataframe


def render() -> None:
    service = require_service()
    render_header("Публікації", "")

    years = service.get_publication_years()
    year_options = ["Усі роки"] + [str(year) for year in years]
    selected_year = st.selectbox("Фільтр за роком", year_options)
    year_value = None if selected_year == "Усі роки" else int(selected_year)

    publication_rows = service.get_publications(year=year_value)
    publications_table = publications_dataframe(publication_rows)

    if publications_table.empty:
        render_empty_state(
            "Публікацій не знайдено",
            "За вибраним роком записів немає. Спробуйте інший рік або перегляньте всі доступні публікації.",
        )
        return

    publications_count = len(publication_rows)
    authorship_links = sum(int(row.get("authors_count", 0) or 0) for row in publication_rows)
    covered_years = len({row.get("year") for row in publication_rows if row.get("year") is not None})

    metrics = st.columns(3, gap="medium")
    with metrics[0]:
        render_summary_strip("Публікації", str(publications_count))
    with metrics[1]:
        render_summary_strip("Авторські входження", str(authorship_links))
    with metrics[2]:
        render_summary_strip("Охоплені роки", str(covered_years))

    publication_map = {
        f"{row['title']} ({row['year'] if row['year'] is not None else 'н/д'})": row
        for row in publication_rows
    }

    layout = st.columns([1.16, 0.94], gap="large")
    with layout[0]:
        render_section_heading("Таблиця публікацій")
        st.dataframe(publications_table, use_container_width=True, hide_index=True)

    with layout[1]:
        render_section_heading("Деталі публікації")
        selected_publication_label = st.selectbox(
            "Обрати публікацію",
            list(publication_map.keys()),
        )
        selected_publication = publication_map[selected_publication_label]

        render_key_value_card(
            "Коротка інформація",
            [
                ("Назва", selected_publication["title"]),
                ("Рік", str(selected_publication["year"] or "н/д")),
                ("Тип", selected_publication["pub_type"]),
                ("Джерело", selected_publication["source"]),
                ("DOI", selected_publication["doi"]),
                ("Кількість авторів", str(selected_publication["authors_count"] or 0)),
            ],
        )
        render_key_value_card(
            "Авторський склад",
            [
                ("Автори", ", ".join(selected_publication["authors"]) if selected_publication["authors"] else "—"),
            ],
        )
