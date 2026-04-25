from __future__ import annotations

import pandas as pd
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


FLASH_KEY = "data_center_flash"
PROBLEM_STATUSES = ["Кандидат", "Потребує перевірки"]


def _show_flash_message() -> None:
    message = st.session_state.pop(FLASH_KEY, "")
    if message:
        st.success(message)


def _teacher_gap_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    renamed = frame.rename(
        columns={
            "id": "ID",
            "full_name": "ПІБ",
            "department_name": "Кафедра",
            "faculty_name": "Факультет",
            "publications": "Публікації",
        }
    )
    columns = ["ID", "ПІБ", "Кафедра", "Факультет", "Публікації"]
    return renamed[columns]


def _problem_publication_option(row: dict[str, object]) -> str:
    year = row.get("year")
    year_label = str(year) if year is not None else "н/д"
    status = str(row.get("status") or "")
    return f"{row.get('title', 'Без назви')} ({year_label}) | {status}"


def render() -> None:
    service = require_service()
    render_header("Центр даних")
    _show_flash_message()

    all_teachers = service.get_teachers()
    all_publications = service.get_publications()

    problematic_publications = [row for row in all_publications if row.get("status") in PROBLEM_STATUSES]
    teachers_without_profiles = [
        row
        for row in all_teachers
        if not any(str(row.get(key) or "").strip() for key in ("orcid", "google_scholar", "scopus", "web_of_science"))
    ]
    teachers_without_publications = [row for row in all_teachers if int(row.get("publications", 0) or 0) == 0]

    summary = st.columns(4, gap="medium")
    with summary[0]:
        render_summary_strip("Проблемні роботи", str(len(problematic_publications)))
    with summary[1]:
        render_summary_strip("Без зовнішніх профілів", str(len(teachers_without_profiles)))
    with summary[2]:
        render_summary_strip("Без публікацій", str(len(teachers_without_publications)))
    with summary[3]:
        render_summary_strip("Усього записів", str(len(all_publications)))

    render_section_heading("Керування проблемними публікаціями")
    publication_filters = st.columns([1.2, 0.8], gap="large")
    search_value = publication_filters[0].text_input(
        "Пошук за назвою або DOI",
        placeholder="Введіть фрагмент назви, DOI або джерело",
    ).strip().lower()
    status_filter = publication_filters[1].selectbox(
        "Показати статус",
        ["Усі проблемні", "Кандидат", "Потребує перевірки"],
    )

    filtered_problematic = problematic_publications
    if status_filter != "Усі проблемні":
        filtered_problematic = [row for row in filtered_problematic if row.get("status") == status_filter]
    if search_value:
        filtered_problematic = [
            row
            for row in filtered_problematic
            if search_value in str(row.get("title") or "").lower()
            or search_value in str(row.get("doi") or "").lower()
            or search_value in str(row.get("source") or "").lower()
        ]

    problem_layout = st.columns([1.15, 0.85], gap="large")
    with problem_layout[0]:
        if filtered_problematic:
            st.dataframe(publications_dataframe(filtered_problematic), use_container_width=True, hide_index=True)
        else:
            render_empty_state(
                "Проблемних публікацій не знайдено",
                "Після фільтрації немає записів, які потребують ручної уваги.",
            )

    with problem_layout[1]:
        if filtered_problematic:
            publication_map = {_problem_publication_option(row): row for row in filtered_problematic}
            selected_label = st.selectbox("Обрати запис", list(publication_map.keys()))
            selected_publication = publication_map[selected_label]
            publication_id = str(selected_publication.get("id") or "").strip()
            details = service.get_publication_management_details(publication_id) or {}
            confidence = float(selected_publication.get("confidence") or 0.0)

            render_key_value_card(
                "Швидка перевірка",
                [
                    ("Статус", str(selected_publication.get("status") or "")),
                    ("Рівень довіри", f"{confidence:.2f}"),
                    ("Джерело", str(selected_publication.get("source") or "Невідомо")),
                    ("Пов'язані викладачі", str(details.get("linked_teachers_count") or 0)),
                ],
            )
            render_key_value_card(
                "Пов'язаний контур",
                [
                    ("Назва", str(details.get("title") or selected_publication.get("title") or "")),
                    ("Рік", str(details.get("year") or selected_publication.get("year") or "н/д")),
                    (
                        "Викладачі",
                        ", ".join(str(item) for item in details.get("linked_teachers", []) if item) or "Немає",
                    ),
                ],
            )

            delete_confirm = st.checkbox(
                "Підтверджую повне видалення вибраної публікації",
                key=f"data_center_delete_{publication_id}",
            )
            if st.button(
                "Видалити проблемну публікацію",
                key=f"data_center_delete_button_{publication_id}",
                use_container_width=True,
                type="primary",
            ):
                if not delete_confirm:
                    st.warning("Спочатку підтвердіть видалення запису.")
                elif service.delete_publication(publication_id):
                    st.session_state[FLASH_KEY] = "Проблемну публікацію видалено з бази."
                    st.rerun()
                else:
                    st.error("Не вдалося видалити запис. Спробуйте ще раз.")
        else:
            render_empty_state(
                "Немає запису для дії",
                "Обраний фільтр не повернув проблемних публікацій.",
            )

    teacher_sections = st.columns(2, gap="large")
    with teacher_sections[0]:
        render_section_heading("Викладачі без зовнішніх профілів")
        without_profiles_frame = _teacher_gap_frame(teachers_without_profiles)
        if without_profiles_frame.empty:
            render_empty_state(
                "Усі мають профілі",
                "Зараз кожен викладач має хоча б один зовнішній ідентифікатор.",
            )
        else:
            st.dataframe(without_profiles_frame, use_container_width=True, hide_index=True)

    with teacher_sections[1]:
        render_section_heading("Викладачі без знайдених публікацій")
        without_publications_frame = _teacher_gap_frame(teachers_without_publications)
        if without_publications_frame.empty:
            render_empty_state(
                "Усі мають знайдені роботи",
                "Зараз у вибірці немає викладачів без жодної публікації.",
            )
        else:
            st.dataframe(without_publications_frame, use_container_width=True, hide_index=True)
