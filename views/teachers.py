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
from ui.formatters import coauthors_dataframe, teacher_publications_dataframe, teachers_dataframe


STATUS_ORDER = [
    "Офіційно підтверджено",
    "Підтверджено",
    "Кандидат",
    "Потребує перевірки",
]


def _profile_count(profile: dict[str, object]) -> int:
    return sum(
        1
        for key in ("orcid", "google_scholar", "scopus", "web_of_science")
        if str(profile.get(key) or "").strip()
    )


def _profile_readiness(profile: dict[str, object], publications: list[dict[str, object]]) -> tuple[str, str]:
    profile_count = _profile_count(profile)
    publications_count = len(publications)
    official_count = sum(1 for row in publications if row.get("status") == "Офіційно підтверджено")

    if profile_count >= 3 and (publications_count >= 5 or official_count >= 1):
        return "Висока", "Профіль добре підготовлений до автоматичного імпорту та перевірки."
    if profile_count >= 2 and publications_count >= 1:
        return "Середня", "Є кілька зовнішніх профілів і вже знайдені роботи."
    if profile_count >= 1:
        return "Базова", "Початкові ідентифікатори є, але варто розширити покриття джерел."
    return "Низька", "Профіль ще потребує ORCID, Scopus, WoS або Scholar для кращого матчингу."


def _profile_status(value: str) -> str:
    return value if value else "Немає"


def _sync_caption(profile: dict[str, object]) -> str:
    synced_at = str(profile.get("last_publication_sync_at") or "").strip()
    trigger = str(profile.get("last_publication_sync_trigger") or "").strip()
    status = str(profile.get("last_publication_sync_status") or "").strip()
    if not synced_at:
        return "Ще не запускалося"

    parts = [synced_at]
    if trigger:
        parts.append(trigger)
    if status:
        parts.append(status)
    return " | ".join(parts)


def _status_counts(publications: list[dict[str, object]]) -> dict[str, int]:
    counts = {status: 0 for status in STATUS_ORDER}
    for row in publications:
        status = str(row.get("status") or "").strip()
        if status in counts:
            counts[status] += 1
    return counts


def render() -> None:
    service = require_service()
    render_header("Викладачі")

    departments = service.get_departments()
    department_labels = {"Усі кафедри": ""}
    for row in departments:
        department_labels[f"{row['name']} ({row['code']})"] = row["code"]

    filters = st.columns([1.45, 1.05], gap="large")
    search_value = filters[0].text_input("Пошук за ПІБ", placeholder="Введіть прізвище або частину імені")
    selected_department_label = filters[1].selectbox("Фільтр за кафедрою", list(department_labels.keys()))
    selected_department_code = department_labels[selected_department_label]

    teacher_rows = service.get_teachers(search=search_value, department_code=selected_department_code)
    teachers_table = teachers_dataframe(teacher_rows)

    if teachers_table.empty:
        render_empty_state(
            "Викладачів не знайдено",
            "Спробуйте змінити пошук або послабити фільтр за кафедрою.",
        )
        return

    teacher_count = len(teacher_rows)
    publications_count = sum(int(row.get("publications", 0) or 0) for row in teacher_rows)
    ready_profiles_count = sum(
        1
        for row in teacher_rows
        if any(str(row.get(key) or "").strip() for key in ("orcid", "google_scholar", "scopus", "web_of_science"))
    )
    departments_count = len({row.get("department_code") for row in teacher_rows if row.get("department_code")})

    metrics = st.columns(4, gap="medium")
    with metrics[0]:
        render_summary_strip("Викладачі у вибірці", str(teacher_count))
    with metrics[1]:
        render_summary_strip("Публікації у вибірці", str(publications_count))
    with metrics[2]:
        render_summary_strip("Профілі для імпорту", str(ready_profiles_count), "Є хоча б один зовнішній ідентифікатор.")
    with metrics[3]:
        render_summary_strip("Кафедри у вибірці", str(departments_count))

    teacher_labels = {f"{row['full_name']} | {row['department_name']}": row["id"] for row in teacher_rows}
    layout = st.columns([1.18, 0.94], gap="large")

    with layout[0]:
        render_section_heading("Таблиця викладачів")
        st.dataframe(teachers_table, use_container_width=True, hide_index=True)

    with layout[1]:
        render_section_heading("Картка викладача")
        selected_teacher_label = st.selectbox("Обрати викладача", list(teacher_labels.keys()))
        selected_teacher_id = teacher_labels[selected_teacher_label]

        profile = service.get_teacher_profile(selected_teacher_id)
        if profile is None:
            render_empty_state(
                "Профіль тимчасово недоступний",
                "Не вдалося знайти детальну картку цього викладача.",
            )
            return

        publications = service.get_teacher_publications(selected_teacher_id)
        coauthors = service.get_teacher_coauthors(selected_teacher_id)
        readiness_label, readiness_caption = _profile_readiness(profile, publications)
        status_counts = _status_counts(publications)

        spotlight = st.columns(2, gap="medium")
        with spotlight[0]:
            render_summary_strip("Готовність профілю", readiness_label, readiness_caption)
        with spotlight[1]:
            render_summary_strip("Останнє оновлення", _sync_caption(profile))

        counters = st.columns(4, gap="medium")
        counters[0].metric("Публікації", len(publications))
        counters[1].metric("Співавтори", len(coauthors))
        counters[2].metric("Підтверджені", status_counts["Офіційно підтверджено"] + status_counts["Підтверджено"])
        counters[3].metric("Кандидати", status_counts["Кандидат"])

        render_key_value_card(
            "Паспорт викладача",
            [
                ("ПІБ", str(profile.get("full_name") or "")),
                ("Кафедра", str(profile.get("department_name") or "")),
                ("Факультет", str(profile.get("faculty_name") or "")),
                ("Посада", str(profile.get("position") or "")),
                ("Науковий ступінь", str(profile.get("academic_degree") or "")),
                ("Вчене звання", str(profile.get("academic_title") or "")),
            ],
        )
        render_key_value_card(
            "Зовнішні профілі",
            [
                ("ORCID", _profile_status(str(profile.get("orcid") or "").strip())),
                ("Google Scholar", _profile_status(str(profile.get("google_scholar") or "").strip())),
                ("Scopus", _profile_status(str(profile.get("scopus") or "").strip())),
                ("Web of Science", _profile_status(str(profile.get("web_of_science") or "").strip())),
                ("Профіль KSPU", _profile_status(str(profile.get("profile_url") or "").strip())),
            ],
        )
        render_key_value_card(
            "Статуси робіт",
            [
                ("Офіційно підтверджено", str(status_counts["Офіційно підтверджено"])),
                ("Підтверджено", str(status_counts["Підтверджено"])),
                ("Кандидат", str(status_counts["Кандидат"])),
                ("Потребує перевірки", str(status_counts["Потребує перевірки"])),
            ],
        )

    tabs = st.tabs(["Публікації викладача", "Співавтори"])

    with tabs[0]:
        render_section_heading("Публікації викладача")
        available_statuses = [status for status in STATUS_ORDER if status_counts[status] > 0]
        publication_status_filter = st.selectbox(
            "Показати статус",
            ["Усі статуси"] + available_statuses,
            key="teacher_publication_status_filter",
        )
        filtered_publications = (
            publications
            if publication_status_filter == "Усі статуси"
            else [row for row in publications if row.get("status") == publication_status_filter]
        )
        publications_table = teacher_publications_dataframe(filtered_publications)
        if publications_table.empty:
            render_empty_state(
                "Публікацій не знайдено",
                "Для цього викладача ще немає робіт у вибраному статусі.",
            )
        else:
            st.dataframe(publications_table, use_container_width=True, hide_index=True)

    with tabs[1]:
        render_section_heading("Співавтори")
        coauthors_table = coauthors_dataframe(coauthors)
        if coauthors_table.empty:
            render_empty_state(
                "Співавторів не виявлено",
                "У мережі ще не зафіксовано спільних робіт з іншими викладачами.",
            )
        else:
            st.dataframe(coauthors_table, use_container_width=True, hide_index=True)
