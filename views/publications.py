from __future__ import annotations

import streamlit as st

from config import is_admin_mode
from ui.components import (
    render_empty_state,
    render_adaptive_dataframe,
    render_fullscreen_dataframe_heading,
    render_header,
    render_key_value_card,
    render_section_heading,
    render_summary_strip,
    require_service,
)
from ui.formatters import publications_dataframe_admin, publications_dataframe_public


STATUS_ORDER = [
    "Офіційно підтверджено",
    "Підтверджено",
    "Кандидат",
    "Потребує перевірки",
    "Відхилено",
    "В чорному списку",
]

PUBLICATION_FLASH_KEY = "publication_management_flash"


def _csv_bytes(frame):
    return frame.to_csv(index=False).encode("utf-8-sig")


def _status_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    counts = {status: 0 for status in STATUS_ORDER}
    for row in rows:
        status = str(row.get("status") or "").strip()
        if status in counts:
            counts[status] += 1
    return counts


def _source_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        source = str(row.get("source") or "").strip() or "Невідомо"
        counts[source] = counts.get(source, 0) + 1
    return counts


def _show_flash_message() -> None:
    message = st.session_state.pop(PUBLICATION_FLASH_KEY, "")
    if message:
        st.success(message)


def _publication_option(row: dict[str, object]) -> str:
    year = row.get("year")
    year_label = str(year) if year is not None else "н/д"
    return f"{row.get('title', 'Без назви')} ({year_label})"


def _teacher_option(row: dict[str, object]) -> str:
    return f"{row.get('full_name', 'Без ПІБ')} | {row.get('department_name', 'Без кафедри')} | {row.get('id', '')}"


def _workspace_option(row: dict[str, object]) -> str:
    year = row.get("year")
    year_label = str(year) if year is not None else "н/д"
    return (
        f"{row.get('title', 'Без назви')} | "
        f"{year_label} | "
        f"{row.get('status', '')} | "
        f"{row.get('id', '')}"
    )


def _render_review_shortcuts(service, publication_id: str, review_note: str, *, key_prefix: str) -> None:
    top = st.columns(2, gap="medium")
    if top[0].button("Підтвердити", key=f"{key_prefix}_confirm_{publication_id}", use_container_width=True):
        if service.set_publication_review_status(publication_id, "Підтверджено", review_note=review_note):
            st.session_state[PUBLICATION_FLASH_KEY] = "Статус публікації оновлено."
            st.rerun()
    if top[1].button("Відхилити", key=f"{key_prefix}_reject_{publication_id}", use_container_width=True):
        if service.set_publication_review_status(publication_id, "Відхилено", review_note=review_note):
            st.session_state[PUBLICATION_FLASH_KEY] = "Публікацію відхилено."
            st.rerun()

    bottom = st.columns(2, gap="medium")
    if bottom[0].button("В чорний список", key=f"{key_prefix}_blacklist_{publication_id}", use_container_width=True):
        if service.set_publication_review_status(publication_id, "В чорному списку", review_note=review_note):
            st.session_state[PUBLICATION_FLASH_KEY] = "Публікацію додано до чорного списку."
            st.rerun()
    if bottom[1].button("Скинути ручний статус", key=f"{key_prefix}_reset_{publication_id}", use_container_width=True):
        if service.clear_publication_review_status(publication_id):
            st.session_state[PUBLICATION_FLASH_KEY] = "Ручний статус скинуто."
            st.rerun()


def _render_bulk_workspace_actions(service, rows: list[dict[str, object]], *, key_prefix: str) -> None:
    render_key_value_card(
        "Групова дія",
        [
            ("Позначено записів", str(len(rows))),
            ("Статуси", ", ".join(sorted({str(row.get('status') or '') for row in rows if row.get('status')})) or "—"),
        ],
    )
    bulk_status = st.selectbox(
        "Новий статус для вибірки",
        STATUS_ORDER[:6],
        key=f"{key_prefix}_status",
    )
    bulk_note = st.text_area(
        "Нотатка для вибірки",
        key=f"{key_prefix}_note",
        height=100,
        placeholder="Наприклад: перевірено вручну або хибний матч.",
    )
    selected_ids = [str(row.get("id") or "").strip() for row in rows if row.get("id")]

    action_columns = st.columns(2, gap="medium")
    if action_columns[0].button(
        "Застосувати статус",
        key=f"{key_prefix}_apply",
        use_container_width=True,
    ):
        updated = service.bulk_set_publication_review_status(selected_ids, bulk_status, review_note=bulk_note)
        st.session_state[PUBLICATION_FLASH_KEY] = f"Масово оновлено {updated} публікацій."
        st.rerun()

    delete_confirm = st.checkbox(
        "Підтверджую масове видалення",
        key=f"{key_prefix}_delete_confirm",
    )
    if action_columns[1].button(
        "Видалити вибране",
        key=f"{key_prefix}_delete",
        use_container_width=True,
        type="primary",
    ):
        if not delete_confirm:
            st.warning("Підтвердіть видалення вибраних записів.")
        else:
            deleted = service.bulk_delete_publications(selected_ids)
            st.session_state[PUBLICATION_FLASH_KEY] = f"Масово видалено {deleted} публікацій."
            st.rerun()


def _render_publication_editor(
    service,
    selected_publication: dict[str, object],
    all_teachers: list[dict[str, object]],
    *,
    key_prefix: str,
) -> None:
    publication_id = str(selected_publication.get("id") or "").strip()
    details = service.get_publication_management_details(publication_id) or {}

    confidence = float(selected_publication.get("confidence") or 0.0)
    confidence_label = f"{confidence:.2f}"

    render_key_value_card(
        "Статус і верифікація",
        [
            ("Статус", str(selected_publication.get("status") or "")),
            ("Рівень довіри", confidence_label),
            ("Джерело", str(selected_publication.get("source") or "Невідомо")),
            ("Тип", str(selected_publication.get("pub_type") or "Невідомо")),
        ],
    )
    render_key_value_card(
        "Коротка інформація",
        [
            ("Назва", str(selected_publication.get("title") or "")),
            ("Рік", str(selected_publication.get("year") or "н/д")),
            ("DOI", str(selected_publication.get("doi") or "Немає")),
            ("Кількість авторів", str(selected_publication.get("authors_count") or 0)),
        ],
    )
    render_key_value_card(
        "Вплив на базу",
        [
            ("Пов'язані викладачі", str(details.get("linked_teachers_count") or 0)),
            (
                "Список викладачів",
                ", ".join(str(item) for item in details.get("linked_teachers", []) if item) or "Немає",
            ),
        ],
    )
    linked_teacher_ids = {
        str(item).strip() for item in details.get("linked_teacher_ids", []) if str(item or "").strip()
    }
    review_note = st.text_area(
        "Нотатка модератора",
        value=str(details.get("review_note") or selected_publication.get("review_note") or ""),
        height=100,
        key=f"{key_prefix}_review_note_{publication_id}",
    )
    render_key_value_card(
        "Авторський склад",
        [
            (
                "Автори",
                ", ".join(selected_publication["authors"]) if selected_publication.get("authors") else "Немає даних",
            ),
        ],
    )

    with st.expander("Модерація", expanded=False):
        _render_review_shortcuts(service, publication_id, review_note, key_prefix=key_prefix)
        edit_columns = st.columns(2, gap="medium")
        edited_year_raw = edit_columns[0].text_input(
            "Рік",
            value="" if details.get("year") is None else str(details.get("year")),
            key=f"{key_prefix}_year_{publication_id}",
        )
        edited_confidence = edit_columns[1].slider(
            "Рівень довіри",
            min_value=0.0,
            max_value=1.0,
            value=float(details.get("confidence") or selected_publication.get("confidence") or 0.0),
            step=0.01,
            key=f"{key_prefix}_confidence_{publication_id}",
        )
        edited_title = st.text_input(
            "Назва",
            value=str(details.get("title") or selected_publication.get("title") or ""),
            key=f"{key_prefix}_title_{publication_id}",
        )
        edited_doi = st.text_input(
            "DOI",
            value=str(details.get("doi") or selected_publication.get("doi") or ""),
            key=f"{key_prefix}_doi_{publication_id}",
        )
        edited_pub_type = st.text_input(
            "Тип",
            value=str(details.get("pub_type") or selected_publication.get("pub_type") or ""),
            key=f"{key_prefix}_type_{publication_id}",
        )
        edited_source = st.text_input(
            "Джерело",
            value=str(details.get("source") or selected_publication.get("source") or ""),
            key=f"{key_prefix}_source_{publication_id}",
        )
        if st.button(
            "Зберегти редагування",
            key=f"{key_prefix}_save_{publication_id}",
            use_container_width=True,
        ):
            edited_year = int(edited_year_raw) if edited_year_raw.strip().isdigit() else None
            if service.update_publication_metadata(
                publication_id,
                title=edited_title,
                year=edited_year,
                doi=edited_doi,
                pub_type=edited_pub_type,
                source=edited_source,
                confidence=edited_confidence,
                review_note=review_note,
            ):
                st.session_state[PUBLICATION_FLASH_KEY] = "Зміни по публікації збережено."
                st.rerun()
            st.error("Не вдалося зберегти редагування.")

    with st.expander("Керування авторством", expanded=False):
        teacher_search = st.text_input(
            "Знайти викладача для прив'язування",
            placeholder="Введіть ПІБ або кафедру",
            key=f"{key_prefix}_teacher_search_{publication_id}",
        ).strip().lower()
        available_teachers = [
            row
            for row in all_teachers
            if str(row.get("id") or "").strip() not in linked_teacher_ids
            and (
                not teacher_search
                or teacher_search in str(row.get("full_name") or "").lower()
                or teacher_search in str(row.get("department_name") or "").lower()
            )
        ]
        teacher_map = {_teacher_option(row): row for row in available_teachers[:120]}
        link_columns = st.columns([1.2, 0.8], gap="medium")
        if teacher_map:
            selected_teacher_label = link_columns[0].selectbox(
                "Додати викладача до публікації",
                list(teacher_map.keys()),
                key=f"{key_prefix}_link_teacher_{publication_id}",
            )
            selected_teacher = teacher_map[selected_teacher_label]
            if link_columns[1].button(
                "Прив'язати викладача",
                key=f"{key_prefix}_link_button_{publication_id}",
                use_container_width=True,
            ):
                teacher_id = str(selected_teacher.get("id") or "").strip()
                if service.create_teacher_publication_link(teacher_id, publication_id):
                    st.session_state[PUBLICATION_FLASH_KEY] = "Викладача прив'язано до публікації."
                    st.rerun()
                st.error("Не вдалося прив'язати викладача.")
        else:
            st.caption("Немає доступних викладачів для прив'язування за поточним фільтром.")

        linked_rows = [
            row for row in all_teachers if str(row.get("id") or "").strip() in linked_teacher_ids
        ]
        linked_map = {_teacher_option(row): row for row in linked_rows}
        if linked_map:
            unlink_columns = st.columns([1.2, 0.8], gap="medium")
            selected_linked_label = unlink_columns[0].selectbox(
                "Відв'язати викладача",
                list(linked_map.keys()),
                key=f"{key_prefix}_unlink_teacher_{publication_id}",
            )
            unlink_confirm = st.checkbox(
                "Підтверджую видалення зв'язку автора з цією публікацією",
                key=f"{key_prefix}_unlink_confirm_{publication_id}",
            )
            if unlink_columns[1].button(
                "Видалити зв'язок",
                key=f"{key_prefix}_unlink_button_{publication_id}",
                use_container_width=True,
            ):
                if not unlink_confirm:
                    st.warning("Спочатку підтвердіть видалення зв'язку.")
                else:
                    linked_teacher = linked_map[selected_linked_label]
                    teacher_id = str(linked_teacher.get("id") or "").strip()
                    if service.delete_teacher_publication_link(teacher_id, publication_id):
                        st.session_state[PUBLICATION_FLASH_KEY] = "Зв'язок автора з публікацією видалено."
                        st.rerun()
                    st.error("Не вдалося видалити зв'язок.")

    with st.expander("Керування записом", expanded=False):
        delete_confirm = st.checkbox(
            "Підтверджую повне видалення цієї публікації з бази",
            key=f"{key_prefix}_delete_confirm_{publication_id}",
        )
        if st.button(
            "Видалити публікацію з бази",
            key=f"{key_prefix}_delete_button_{publication_id}",
            use_container_width=True,
            type="primary",
        ):
            if not delete_confirm:
                st.warning("Спочатку підтвердіть видалення запису.")
            elif service.delete_publication(publication_id):
                st.session_state[PUBLICATION_FLASH_KEY] = "Публікацію видалено з бази."
                st.rerun()
            else:
                st.error("Не вдалося видалити публікацію. Спробуйте ще раз.")


def _render_publication_details(selected_publication: dict[str, object]) -> None:
    render_key_value_card(
        "Коротка інформація",
        [
            ("Назва", str(selected_publication.get("title") or "")),
            ("Рік", str(selected_publication.get("year") or "н/д")),
            ("DOI", str(selected_publication.get("doi") or "Немає")),
            ("Тип", str(selected_publication.get("pub_type") or "Невідомо")),
            ("Джерело", str(selected_publication.get("source") or "Невідомо")),
            ("Статус", str(selected_publication.get("status") or "Невідомо")),
            ("Кількість авторів", str(selected_publication.get("authors_count") or 0)),
        ],
    )
    render_key_value_card(
        "Авторський склад",
        [
            (
                "Автори",
                ", ".join(str(author) for author in selected_publication.get("authors", []) if author) or "Немає даних",
            ),
        ],
    )


if hasattr(st, "dialog"):
    @st.dialog("Робоча панель публікацій", width="large")
    def _publication_workspace_dialog(service, rows: list[dict[str, object]], all_teachers: list[dict[str, object]]) -> None:
        st.caption("Велика панель для масового відбору, модерації та редагування публікацій.")
        if not rows:
            render_empty_state("Публікацій немає", "Для поточного фільтра немає записів, які можна відкрити в панелі.")
            return

        search = st.text_input(
            "Пошук усередині панелі",
            placeholder="Назва, DOI, джерело або статус",
            key="publication_workspace_search",
        ).strip().lower()
        visible_rows = rows
        if search:
            visible_rows = [
                row
                for row in visible_rows
                if search in str(row.get("title") or "").lower()
                or search in str(row.get("doi") or "").lower()
                or search in str(row.get("source") or "").lower()
                or search in str(row.get("status") or "").lower()
            ]

        option_map = {_workspace_option(row): row for row in visible_rows}
        current_selection = [
            label for label in st.session_state.get("publication_workspace_selection", []) if label in option_map
        ]

        top_controls = st.columns([0.9, 0.9, 1.2], gap="medium")
        if top_controls[0].button("Позначити все видиме", key="publication_workspace_select_all", use_container_width=True):
            st.session_state["publication_workspace_selection"] = list(option_map.keys())
            st.rerun()
        if top_controls[1].button("Очистити вибір", key="publication_workspace_clear", use_container_width=True):
            st.session_state["publication_workspace_selection"] = []
            st.rerun()
        top_controls[2].caption(f"У списку: {len(visible_rows)} | Позначено: {len(current_selection)}")

        selected_labels = st.multiselect(
            "Вибір записів",
            list(option_map.keys()),
            default=current_selection,
            key="publication_workspace_selection",
            placeholder="Позначте конкретні публікації або весь поточний зріз",
        )
        selected_rows = [option_map[label] for label in selected_labels if label in option_map]

        workspace = st.columns([1.22, 0.78], gap="large")
        with workspace[0]:
            render_adaptive_dataframe(publications_dataframe_admin(visible_rows), use_container_width=True, hide_index=True, height=620)

        with workspace[1]:
            if len(selected_rows) == 1:
                _render_publication_editor(service, selected_rows[0], all_teachers, key_prefix="workspace_publication")
            elif len(selected_rows) > 1:
                _render_bulk_workspace_actions(service, selected_rows, key_prefix="workspace_bulk")
            else:
                render_empty_state(
                    "Немає вибору",
                    "Оберіть одну публікацію для детального редагування або кілька для масової дії.",
                )
else:
    def _publication_workspace_dialog(service, rows: list[dict[str, object]], all_teachers: list[dict[str, object]]) -> None:
        del service, rows, all_teachers
        st.info("Для цього середовища повна панель недоступна. Скористайтеся стандартним блоком деталей праворуч.")


def render() -> None:
    service = require_service()
    admin_mode = is_admin_mode()
    render_header("Публікації", "Каталог наукових робіт з фільтрами, деталями записів і прив'язкою до викладачів.")
    _show_flash_message()

    years = service.get_publication_years()
    year_options = ["Усі роки"] + [str(year) for year in years]

    all_teachers = service.get_teachers()
    teacher_name_to_department = {
        str(row.get("full_name") or "").strip(): {
            "department_code": str(row.get("department_code") or "").strip(),
            "department_name": str(row.get("department_name") or "").strip(),
        }
        for row in all_teachers
    }
    department_options = {"Усі кафедри": ""}
    for row in all_teachers:
        department_code = str(row.get("department_code") or "").strip()
        department_name = str(row.get("department_name") or "").strip()
        if department_code and department_name:
            department_options[f"{department_name} ({department_code})"] = department_code
    teacher_options = {"Усі викладачі": ""}
    for row in all_teachers:
        teacher_options[str(row.get("full_name") or "").strip()] = str(row.get("full_name") or "").strip()

    filter_rows_top = st.columns(3, gap="large")
    selected_year = filter_rows_top[0].selectbox("Фільтр за роком", year_options)
    year_value = None if selected_year == "Усі роки" else int(selected_year)
    search_query = filter_rows_top[1].text_input("Пошук за назвою або DOI", placeholder="Введіть назву, DOI або фрагмент джерела").strip().lower()
    selected_teacher_name = filter_rows_top[2].selectbox("Фільтр за викладачем", list(teacher_options.keys()))

    publication_rows = service.get_publications(year=year_value)
    status_counts = _status_counts(publication_rows)
    available_statuses = [status for status in STATUS_ORDER if status_counts[status] > 0]
    source_counts = _source_counts(publication_rows)

    filter_rows_bottom = st.columns(4, gap="large")
    selected_department_label = filter_rows_bottom[0].selectbox("Фільтр за кафедрою", list(department_options.keys()))
    selected_department_code = department_options[selected_department_label]
    selected_status = filter_rows_bottom[1].selectbox("Статус робіт", ["Усі статуси"] + available_statuses)
    selected_source = filter_rows_bottom[2].selectbox("Джерело", ["Усі джерела"] + sorted(source_counts.keys()))
    only_coauthored = filter_rows_bottom[3].checkbox("Лише публікації зі співавторами")

    filtered_rows = publication_rows
    if search_query:
        filtered_rows = [
            row
            for row in filtered_rows
            if search_query in str(row.get("title", "")).lower()
            or search_query in str(row.get("doi", "")).lower()
            or search_query in str(row.get("source", "")).lower()
        ]
    if selected_teacher_name != "Усі викладачі":
        filtered_rows = [
            row
            for row in filtered_rows
            if selected_teacher_name in [str(author).strip() for author in row.get("authors", [])]
        ]
    if selected_department_code:
        filtered_rows = [
            row
            for row in filtered_rows
            if any(
                teacher_name_to_department.get(str(author).strip(), {}).get("department_code") == selected_department_code
                for author in row.get("authors", [])
            )
        ]
    if selected_status != "Усі статуси":
        filtered_rows = [row for row in filtered_rows if row.get("status") == selected_status]
    if selected_source != "Усі джерела":
        filtered_rows = [
            row
            for row in filtered_rows
            if (str(row.get("source") or "").strip() or "Невідомо") == selected_source
        ]
    if only_coauthored:
        filtered_rows = [row for row in filtered_rows if int(row.get("authors_count", 0) or 0) > 1]

    publications_table = (
        publications_dataframe_admin(filtered_rows)
        if admin_mode
        else publications_dataframe_public(filtered_rows)
    )

    if publications_table.empty:
        render_empty_state(
            "Публікацій не знайдено",
            "Змініть фільтри або послабте пошук, щоб переглянути доступні роботи.",
        )
        return

    filtered_status_counts = _status_counts(filtered_rows)
    publications_count = len(filtered_rows)
    authorship_links = sum(int(row.get("authors_count", 0) or 0) for row in filtered_rows)
    covered_years = len({row.get("year") for row in filtered_rows if row.get("year") is not None})

    metrics = st.columns(4, gap="medium")
    with metrics[0]:
        render_summary_strip("Публікації", str(publications_count))
    with metrics[1]:
        render_summary_strip(
            "Підтверджені",
            str(filtered_status_counts["Офіційно підтверджено"] + filtered_status_counts["Підтверджено"]),
        )
    with metrics[2]:
        render_summary_strip("Потребують перевірки", str(filtered_status_counts["Потребує перевірки"]))
    with metrics[3]:
        render_summary_strip("Охоплені роки", str(covered_years))

    secondary = st.columns(3, gap="medium")
    secondary[0].metric("Авторські входження", authorship_links)
    secondary[1].metric("Кандидати", filtered_status_counts["Кандидат"])
    secondary[2].metric("Співавторські роботи", sum(1 for row in filtered_rows if int(row.get("authors_count", 0) or 0) > 1))

    publication_map = {_publication_option(row): row for row in filtered_rows}

    layout = st.columns([1.16, 0.94], gap="large")
    with layout[0]:
        render_fullscreen_dataframe_heading(
            "Таблиця публікацій",
            publications_table,
            key="publications_table_fullscreen",
            subtitle="Натисніть на заголовок, щоб відкрити повний перегляд таблиці.",
            caption="Повний зріз відфільтрованих публікацій.",
        )
        controls = st.columns([0.64, 0.36], gap="small")
        if admin_mode:
            if controls[0].button("Відкрити робочу панель", use_container_width=True, key="open_publication_workspace"):
                _publication_workspace_dialog(service, filtered_rows, all_teachers)
        else:
            controls[0].caption("Публічний режим: модерація та редагування приховані.")
        controls[1].download_button(
            "Експорт поточного зрізу CSV",
            _csv_bytes(publications_table),
            file_name="publications_current_slice.csv",
            mime="text/csv",
            use_container_width=True,
        )
        render_adaptive_dataframe(publications_table, use_container_width=True, hide_index=True)

    with layout[1]:
        render_section_heading("Деталі публікації")
        selected_publication_label = st.selectbox("Обрати публікацію", list(publication_map.keys()))
        selected_publication = publication_map[selected_publication_label]
        if admin_mode:
            _render_publication_editor(service, selected_publication, all_teachers, key_prefix="publication")
        else:
            _render_publication_details(selected_publication)
