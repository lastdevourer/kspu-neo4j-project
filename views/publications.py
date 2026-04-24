from __future__ import annotations

import streamlit as st

from services.publication_sources import search_openalex_publications
from ui.components import (
    render_empty_state,
    render_header,
    render_key_value_card,
    render_section_heading,
    render_summary_strip,
    require_service,
)
from ui.formatters import publications_dataframe


def render_import_block(service) -> None:
    render_section_heading("Імпорт публікацій з OpenAlex")

    departments = service.get_departments()
    department_labels = {"Усі кафедри": ""}
    for row in departments:
        department_labels[f"{row['name']} ({row['code']})"] = row["code"]

    cols = st.columns([1.1, 1.1, 0.8], gap="medium")

    selected_department_label = cols[0].selectbox(
        "Кафедра для імпорту",
        list(department_labels.keys()),
        key="publication_import_department",
    )
    selected_department_code = department_labels[selected_department_label]

    from_year = cols[1].number_input(
        "З якого року шукати",
        min_value=1990,
        max_value=2030,
        value=2018,
        step=1,
    )

    per_page = cols[2].slider(
        "Ліміт на викладача",
        min_value=3,
        max_value=25,
        value=10,
        step=1,
    )

    teachers = service.get_teacher_import_options(department_code=selected_department_code)

    if not teachers:
        render_empty_state(
            "Викладачів для імпорту не знайдено",
            "Спочатку завантажте викладачів або змініть фільтр кафедри.",
        )
        return

    teacher_labels = {
        f"{row['full_name']} | {row['department_name']} | зараз публікацій: {row['publications']}": row
        for row in teachers
    }

    selected_teacher_label = st.selectbox(
        "Обрати викладача",
        list(teacher_labels.keys()),
        key="publication_import_teacher",
    )
    selected_teacher = teacher_labels[selected_teacher_label]

    st.caption(
        "Основне джерело — OpenAlex. Google Scholar краще залишити як допоміжний профіль, "
        "бо прямий парсинг Scholar нестабільний і може блокувати запити."
    )

    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        preview_button = st.button("Знайти публікації для одного викладача", type="secondary")

    with col_b:
        bulk_button = st.button("Завантажити публікації всім у вибраній кафедрі", type="primary")

    if preview_button:
        with st.spinner("Шукаю публікації в OpenAlex..."):
            found_publications = search_openalex_publications(
                selected_teacher["full_name"],
                from_year=int(from_year),
                per_page=int(per_page),
            )

        st.session_state["openalex_preview_teacher_id"] = selected_teacher["id"]
        st.session_state["openalex_preview_publications"] = found_publications

    preview_publications = st.session_state.get("openalex_preview_publications", [])
    preview_teacher_id = st.session_state.get("openalex_preview_teacher_id")

    if preview_publications:
        st.success(f"Знайдено публікацій: {len(preview_publications)}")

        preview_rows = [
            {
                "id": row["id"],
                "title": row["title"],
                "year": row["year"],
                "doi": row["doi"],
                "pub_type": row["pub_type"],
                "source": row["source"],
                "authors": row["authors"],
                "authors_count": len(row["authors"]),
            }
            for row in preview_publications
        ]

        st.dataframe(publications_dataframe(preview_rows), use_container_width=True, hide_index=True)

        if st.button("Зберегти ці публікації в Neo4j", type="primary"):
            imported = service.import_teacher_publications(
                teacher_id=preview_teacher_id,
                publications=preview_publications,
            )
            st.success(f"Імпортовано / оновлено публікацій: {imported}")
            st.cache_data.clear()
            st.rerun()

    if bulk_button:
        st.warning(
            "Масовий імпорт краще запускати по одній кафедрі, "
            "щоб зменшити ризик зайвих однофамільних публікацій."
        )

        total_imported = 0
        processed = 0
        failed = 0

        progress = st.progress(0)
        status = st.empty()

        for index, teacher in enumerate(teachers):
            status.write(f"Обробка: {teacher['full_name']}")

            try:
                found_publications = search_openalex_publications(
                    teacher["full_name"],
                    from_year=int(from_year),
                    per_page=int(per_page),
                )

                imported = service.import_teacher_publications(
                    teacher_id=teacher["id"],
                    publications=found_publications,
                )

                total_imported += imported
                processed += 1

            except Exception as error:
                failed += 1
                st.error(f"Помилка для {teacher['full_name']}: {error}")

            progress.progress((index + 1) / len(teachers))

        status.write("Готово")

        st.success(
            f"Оброблено викладачів: {processed}. "
            f"Помилок: {failed}. "
            f"Імпортовано / оновлено публікацій: {total_imported}."
        )

        st.cache_data.clear()


def render() -> None:
    service = require_service()
    render_header("Публікації", "")

    with st.expander("Додати публікації через OpenAlex", expanded=False):
        render_import_block(service)

    years = service.get_publication_years()
    year_options = ["Усі роки"] + [str(year) for year in years]
    selected_year = st.selectbox("Фільтр за роком", year_options)
    year_value = None if selected_year == "Усі роки" else int(selected_year)

    publication_rows = service.get_publications(year=year_value)
    publications_table = publications_dataframe(publication_rows)

    if publications_table.empty:
        render_empty_state(
            "Публікацій не знайдено",
            "За вибраним роком записів немає. Спробуйте імпортувати публікації через OpenAlex.",
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
                (
                    "Автори",
                    ", ".join(selected_publication["authors"])
                    if selected_publication["authors"]
                    else "—",
                ),
            ],
        )
