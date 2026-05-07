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
    "ÐžÑ„Ñ–Ñ†Ñ–Ð¹Ð½Ð¾ Ð¿Ñ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾",
    "ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾",
    "ÐšÐ°Ð½Ð´Ð¸Ð´Ð°Ñ‚",
    "ÐŸÐ¾Ñ‚Ñ€ÐµÐ±ÑƒÑ” Ð¿ÐµÑ€ÐµÐ²Ñ–Ñ€ÐºÐ¸",
    "Ð’Ñ–Ð´Ñ…Ð¸Ð»ÐµÐ½Ð¾",
    "Ð’ Ñ‡Ð¾Ñ€Ð½Ð¾Ð¼Ñƒ ÑÐ¿Ð¸ÑÐºÑƒ",
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
        source = str(row.get("source") or "").strip() or "ÐÐµÐ²Ñ–Ð´Ð¾Ð¼Ð¾"
        counts[source] = counts.get(source, 0) + 1
    return counts


def _show_flash_message() -> None:
    message = st.session_state.pop(PUBLICATION_FLASH_KEY, "")
    if message:
        st.success(message)


def _build_publications_preview_frame(frame, *, admin_mode: bool):
    preview_columns = (
        ["ÐÐ°Ð·Ð²Ð°", "Ð Ñ–Ðº", "Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾"]
        if not admin_mode
        else ["ÐÐ°Ð·Ð²Ð°", "Ð¡Ñ‚Ð°Ñ‚ÑƒÑ", "Ð Ñ–Ðº", "Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾"]
    )
    existing_columns = [column for column in preview_columns if column in frame.columns]
    return frame[existing_columns].copy() if existing_columns else frame


def _publication_option(row: dict[str, object]) -> str:
    year = row.get("year")
    year_label = str(year) if year is not None else "Ð½/Ð´"
    return f"{row.get('title', 'Ð‘ÐµÐ· Ð½Ð°Ð·Ð²Ð¸')} ({year_label})"


def _teacher_option(row: dict[str, object]) -> str:
    return f"{row.get('full_name', 'Ð‘ÐµÐ· ÐŸÐ†Ð‘')} | {row.get('department_name', 'Ð‘ÐµÐ· ÐºÐ°Ñ„ÐµÐ´Ñ€Ð¸')} | {row.get('id', '')}"


def _workspace_option(row: dict[str, object]) -> str:
    year = row.get("year")
    year_label = str(year) if year is not None else "Ð½/Ð´"
    return (
        f"{row.get('title', 'Ð‘ÐµÐ· Ð½Ð°Ð·Ð²Ð¸')} | "
        f"{year_label} | "
        f"{row.get('status', '')} | "
        f"{row.get('id', '')}"
    )


def _render_review_shortcuts(service, publication_id: str, review_note: str, *, key_prefix: str) -> None:
    top = st.columns(2, gap="medium")
    if top[0].button("ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¸Ñ‚Ð¸", key=f"{key_prefix}_confirm_{publication_id}", use_container_width=True):
        if service.set_publication_review_status(publication_id, "ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾", review_note=review_note):
            st.session_state[PUBLICATION_FLASH_KEY] = "Ð¡Ñ‚Ð°Ñ‚ÑƒÑ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ð¾Ð½Ð¾Ð²Ð»ÐµÐ½Ð¾."
            st.rerun()
    if top[1].button("Ð’Ñ–Ð´Ñ…Ð¸Ð»Ð¸Ñ‚Ð¸", key=f"{key_prefix}_reject_{publication_id}", use_container_width=True):
        if service.set_publication_review_status(publication_id, "Ð’Ñ–Ð´Ñ…Ð¸Ð»ÐµÐ½Ð¾", review_note=review_note):
            st.session_state[PUBLICATION_FLASH_KEY] = "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑŽ Ð²Ñ–Ð´Ñ…Ð¸Ð»ÐµÐ½Ð¾."
            st.rerun()

    bottom = st.columns(2, gap="medium")
    if bottom[0].button("Ð’ Ñ‡Ð¾Ñ€Ð½Ð¸Ð¹ ÑÐ¿Ð¸ÑÐ¾Ðº", key=f"{key_prefix}_blacklist_{publication_id}", use_container_width=True):
        if service.set_publication_review_status(publication_id, "Ð’ Ñ‡Ð¾Ñ€Ð½Ð¾Ð¼Ñƒ ÑÐ¿Ð¸ÑÐºÑƒ", review_note=review_note):
            st.session_state[PUBLICATION_FLASH_KEY] = "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑŽ Ð´Ð¾Ð´Ð°Ð½Ð¾ Ð´Ð¾ Ñ‡Ð¾Ñ€Ð½Ð¾Ð³Ð¾ ÑÐ¿Ð¸ÑÐºÑƒ."
            st.rerun()
    if bottom[1].button("Ð¡ÐºÐ¸Ð½ÑƒÑ‚Ð¸ Ñ€ÑƒÑ‡Ð½Ð¸Ð¹ ÑÑ‚Ð°Ñ‚ÑƒÑ", key=f"{key_prefix}_reset_{publication_id}", use_container_width=True):
        if service.clear_publication_review_status(publication_id):
            st.session_state[PUBLICATION_FLASH_KEY] = "Ð ÑƒÑ‡Ð½Ð¸Ð¹ ÑÑ‚Ð°Ñ‚ÑƒÑ ÑÐºÐ¸Ð½ÑƒÑ‚Ð¾."
            st.rerun()


def _render_bulk_workspace_actions(service, rows: list[dict[str, object]], *, key_prefix: str) -> None:
    render_key_value_card(
        "Ð“Ñ€ÑƒÐ¿Ð¾Ð²Ð° Ð´Ñ–Ñ",
        [
            ("ÐŸÐ¾Ð·Ð½Ð°Ñ‡ÐµÐ½Ð¾ Ð·Ð°Ð¿Ð¸ÑÑ–Ð²", str(len(rows))),
            ("Ð¡Ñ‚Ð°Ñ‚ÑƒÑÐ¸", ", ".join(sorted({str(row.get('status') or '') for row in rows if row.get('status')})) or "â€”"),
        ],
    )
    bulk_status = st.selectbox(
        "ÐÐ¾Ð²Ð¸Ð¹ ÑÑ‚Ð°Ñ‚ÑƒÑ Ð´Ð»Ñ Ð²Ð¸Ð±Ñ–Ñ€ÐºÐ¸",
        STATUS_ORDER[:6],
        key=f"{key_prefix}_status",
    )
    bulk_note = st.text_area(
        "ÐÐ¾Ñ‚Ð°Ñ‚ÐºÐ° Ð´Ð»Ñ Ð²Ð¸Ð±Ñ–Ñ€ÐºÐ¸",
        key=f"{key_prefix}_note",
        height=100,
        placeholder="ÐÐ°Ð¿Ñ€Ð¸ÐºÐ»Ð°Ð´: Ð¿ÐµÑ€ÐµÐ²Ñ–Ñ€ÐµÐ½Ð¾ Ð²Ñ€ÑƒÑ‡Ð½Ñƒ Ð°Ð±Ð¾ Ñ…Ð¸Ð±Ð½Ð¸Ð¹ Ð¼Ð°Ñ‚Ñ‡.",
    )
    selected_ids = [str(row.get("id") or "").strip() for row in rows if row.get("id")]

    action_columns = st.columns(2, gap="medium")
    if action_columns[0].button(
        "Ð—Ð°ÑÑ‚Ð¾ÑÑƒÐ²Ð°Ñ‚Ð¸ ÑÑ‚Ð°Ñ‚ÑƒÑ",
        key=f"{key_prefix}_apply",
        use_container_width=True,
    ):
        updated = service.bulk_set_publication_review_status(selected_ids, bulk_status, review_note=bulk_note)
        st.session_state[PUBLICATION_FLASH_KEY] = f"ÐœÐ°ÑÐ¾Ð²Ð¾ Ð¾Ð½Ð¾Ð²Ð»ÐµÐ½Ð¾ {updated} Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹."
        st.rerun()

    delete_confirm = st.checkbox(
        "ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÑƒÑŽ Ð¼Ð°ÑÐ¾Ð²Ðµ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð½Ñ",
        key=f"{key_prefix}_delete_confirm",
    )
    if action_columns[1].button(
        "Ð’Ð¸Ð´Ð°Ð»Ð¸Ñ‚Ð¸ Ð²Ð¸Ð±Ñ€Ð°Ð½Ðµ",
        key=f"{key_prefix}_delete",
        use_container_width=True,
        type="primary",
    ):
        if not delete_confirm:
            st.warning("ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ñ–Ñ‚ÑŒ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð½Ñ Ð²Ð¸Ð±Ñ€Ð°Ð½Ð¸Ñ… Ð·Ð°Ð¿Ð¸ÑÑ–Ð².")
        else:
            deleted = service.bulk_delete_publications(selected_ids)
            st.session_state[PUBLICATION_FLASH_KEY] = f"ÐœÐ°ÑÐ¾Ð²Ð¾ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð¾ {deleted} Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹."
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
        "Ð¡Ñ‚Ð°Ñ‚ÑƒÑ Ñ– Ð²ÐµÑ€Ð¸Ñ„Ñ–ÐºÐ°Ñ†Ñ–Ñ",
        [
            ("Ð¡Ñ‚Ð°Ñ‚ÑƒÑ", str(selected_publication.get("status") or "")),
            ("Ð Ñ–Ð²ÐµÐ½ÑŒ Ð´Ð¾Ð²Ñ–Ñ€Ð¸", confidence_label),
            ("Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾", str(selected_publication.get("source") or "ÐÐµÐ²Ñ–Ð´Ð¾Ð¼Ð¾")),
            ("Ð¢Ð¸Ð¿", str(selected_publication.get("pub_type") or "ÐÐµÐ²Ñ–Ð´Ð¾Ð¼Ð¾")),
        ],
    )
    render_key_value_card(
        "ÐšÐ¾Ñ€Ð¾Ñ‚ÐºÐ° Ñ–Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ñ–Ñ",
        [
            ("ÐÐ°Ð·Ð²Ð°", str(selected_publication.get("title") or "")),
            ("Ð Ñ–Ðº", str(selected_publication.get("year") or "Ð½/Ð´")),
            ("DOI", str(selected_publication.get("doi") or "ÐÐµÐ¼Ð°Ñ”")),
            ("ÐšÑ–Ð»ÑŒÐºÑ–ÑÑ‚ÑŒ Ð°Ð²Ñ‚Ð¾Ñ€Ñ–Ð²", str(selected_publication.get("authors_count") or 0)),
        ],
    )
    render_key_value_card(
        "Ð’Ð¿Ð»Ð¸Ð² Ð½Ð° Ð±Ð°Ð·Ñƒ",
        [
            ("ÐŸÐ¾Ð²'ÑÐ·Ð°Ð½Ñ– Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–", str(details.get("linked_teachers_count") or 0)),
            (
                "Ð¡Ð¿Ð¸ÑÐ¾Ðº Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð²",
                ", ".join(str(item) for item in details.get("linked_teachers", []) if item) or "ÐÐµÐ¼Ð°Ñ”",
            ),
        ],
    )
    linked_teacher_ids = {
        str(item).strip() for item in details.get("linked_teacher_ids", []) if str(item or "").strip()
    }
    review_note = st.text_area(
        "ÐÐ¾Ñ‚Ð°Ñ‚ÐºÐ° Ð¼Ð¾Ð´ÐµÑ€Ð°Ñ‚Ð¾Ñ€Ð°",
        value=str(details.get("review_note") or selected_publication.get("review_note") or ""),
        height=100,
        key=f"{key_prefix}_review_note_{publication_id}",
    )
    render_key_value_card(
        "ÐÐ²Ñ‚Ð¾Ñ€ÑÑŒÐºÐ¸Ð¹ ÑÐºÐ»Ð°Ð´",
        [
            (
                "ÐÐ²Ñ‚Ð¾Ñ€Ð¸",
                ", ".join(selected_publication["authors"]) if selected_publication.get("authors") else "ÐÐµÐ¼Ð°Ñ” Ð´Ð°Ð½Ð¸Ñ…",
            ),
        ],
    )

    with st.expander("ÐœÐ¾Ð´ÐµÑ€Ð°Ñ†Ñ–Ñ", expanded=False):
        _render_review_shortcuts(service, publication_id, review_note, key_prefix=key_prefix)
        edit_columns = st.columns(2, gap="medium")
        edited_year_raw = edit_columns[0].text_input(
            "Ð Ñ–Ðº",
            value="" if details.get("year") is None else str(details.get("year")),
            key=f"{key_prefix}_year_{publication_id}",
        )
        edited_confidence = edit_columns[1].slider(
            "Ð Ñ–Ð²ÐµÐ½ÑŒ Ð´Ð¾Ð²Ñ–Ñ€Ð¸",
            min_value=0.0,
            max_value=1.0,
            value=float(details.get("confidence") or selected_publication.get("confidence") or 0.0),
            step=0.01,
            key=f"{key_prefix}_confidence_{publication_id}",
        )
        edited_title = st.text_input(
            "ÐÐ°Ð·Ð²Ð°",
            value=str(details.get("title") or selected_publication.get("title") or ""),
            key=f"{key_prefix}_title_{publication_id}",
        )
        edited_doi = st.text_input(
            "DOI",
            value=str(details.get("doi") or selected_publication.get("doi") or ""),
            key=f"{key_prefix}_doi_{publication_id}",
        )
        edited_pub_type = st.text_input(
            "Ð¢Ð¸Ð¿",
            value=str(details.get("pub_type") or selected_publication.get("pub_type") or ""),
            key=f"{key_prefix}_type_{publication_id}",
        )
        edited_source = st.text_input(
            "Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾",
            value=str(details.get("source") or selected_publication.get("source") or ""),
            key=f"{key_prefix}_source_{publication_id}",
        )
        if st.button(
            "Ð—Ð±ÐµÑ€ÐµÐ³Ñ‚Ð¸ Ñ€ÐµÐ´Ð°Ð³ÑƒÐ²Ð°Ð½Ð½Ñ",
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
                st.session_state[PUBLICATION_FLASH_KEY] = "Ð—Ð¼Ñ–Ð½Ð¸ Ð¿Ð¾ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ð·Ð±ÐµÑ€ÐµÐ¶ÐµÐ½Ð¾."
                st.rerun()
            st.error("ÐÐµ Ð²Ð´Ð°Ð»Ð¾ÑÑ Ð·Ð±ÐµÑ€ÐµÐ³Ñ‚Ð¸ Ñ€ÐµÐ´Ð°Ð³ÑƒÐ²Ð°Ð½Ð½Ñ.")

    with st.expander("ÐšÐµÑ€ÑƒÐ²Ð°Ð½Ð½Ñ Ð°Ð²Ñ‚Ð¾Ñ€ÑÑ‚Ð²Ð¾Ð¼", expanded=False):
        teacher_search = st.text_input(
            "Ð—Ð½Ð°Ð¹Ñ‚Ð¸ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð° Ð´Ð»Ñ Ð¿Ñ€Ð¸Ð²'ÑÐ·ÑƒÐ²Ð°Ð½Ð½Ñ",
            placeholder="Ð’Ð²ÐµÐ´Ñ–Ñ‚ÑŒ ÐŸÐ†Ð‘ Ð°Ð±Ð¾ ÐºÐ°Ñ„ÐµÐ´Ñ€Ñƒ",
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
                "Ð”Ð¾Ð´Ð°Ñ‚Ð¸ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð° Ð´Ð¾ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—",
                list(teacher_map.keys()),
                key=f"{key_prefix}_link_teacher_{publication_id}",
            )
            selected_teacher = teacher_map[selected_teacher_label]
            if link_columns[1].button(
                "ÐŸÑ€Ð¸Ð²'ÑÐ·Ð°Ñ‚Ð¸ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°",
                key=f"{key_prefix}_link_button_{publication_id}",
                use_container_width=True,
            ):
                teacher_id = str(selected_teacher.get("id") or "").strip()
                if service.create_teacher_publication_link(teacher_id, publication_id):
                    st.session_state[PUBLICATION_FLASH_KEY] = "Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð° Ð¿Ñ€Ð¸Ð²'ÑÐ·Ð°Ð½Ð¾ Ð´Ð¾ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—."
                    st.rerun()
                st.error("ÐÐµ Ð²Ð´Ð°Ð»Ð¾ÑÑ Ð¿Ñ€Ð¸Ð²'ÑÐ·Ð°Ñ‚Ð¸ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°.")
        else:
            st.caption("ÐÐµÐ¼Ð°Ñ” Ð´Ð¾ÑÑ‚ÑƒÐ¿Ð½Ð¸Ñ… Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð² Ð´Ð»Ñ Ð¿Ñ€Ð¸Ð²'ÑÐ·ÑƒÐ²Ð°Ð½Ð½Ñ Ð·Ð° Ð¿Ð¾Ñ‚Ð¾Ñ‡Ð½Ð¸Ð¼ Ñ„Ñ–Ð»ÑŒÑ‚Ñ€Ð¾Ð¼.")

        linked_rows = [
            row for row in all_teachers if str(row.get("id") or "").strip() in linked_teacher_ids
        ]
        linked_map = {_teacher_option(row): row for row in linked_rows}
        if linked_map:
            unlink_columns = st.columns([1.2, 0.8], gap="medium")
            selected_linked_label = unlink_columns[0].selectbox(
                "Ð’Ñ–Ð´Ð²'ÑÐ·Ð°Ñ‚Ð¸ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°",
                list(linked_map.keys()),
                key=f"{key_prefix}_unlink_teacher_{publication_id}",
            )
            unlink_confirm = st.checkbox(
                "ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÑƒÑŽ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð½Ñ Ð·Ð²'ÑÐ·ÐºÑƒ Ð°Ð²Ñ‚Ð¾Ñ€Ð° Ð· Ñ†Ñ–Ñ”ÑŽ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ”ÑŽ",
                key=f"{key_prefix}_unlink_confirm_{publication_id}",
            )
            if unlink_columns[1].button(
                "Ð’Ð¸Ð´Ð°Ð»Ð¸Ñ‚Ð¸ Ð·Ð²'ÑÐ·Ð¾Ðº",
                key=f"{key_prefix}_unlink_button_{publication_id}",
                use_container_width=True,
            ):
                if not unlink_confirm:
                    st.warning("Ð¡Ð¿Ð¾Ñ‡Ð°Ñ‚ÐºÑƒ Ð¿Ñ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ñ–Ñ‚ÑŒ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð½Ñ Ð·Ð²'ÑÐ·ÐºÑƒ.")
                else:
                    linked_teacher = linked_map[selected_linked_label]
                    teacher_id = str(linked_teacher.get("id") or "").strip()
                    if service.delete_teacher_publication_link(teacher_id, publication_id):
                        st.session_state[PUBLICATION_FLASH_KEY] = "Ð—Ð²'ÑÐ·Ð¾Ðº Ð°Ð²Ñ‚Ð¾Ñ€Ð° Ð· Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ”ÑŽ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð¾."
                        st.rerun()
                    st.error("ÐÐµ Ð²Ð´Ð°Ð»Ð¾ÑÑ Ð²Ð¸Ð´Ð°Ð»Ð¸Ñ‚Ð¸ Ð·Ð²'ÑÐ·Ð¾Ðº.")

    with st.expander("ÐšÐµÑ€ÑƒÐ²Ð°Ð½Ð½Ñ Ð·Ð°Ð¿Ð¸ÑÐ¾Ð¼", expanded=False):
        delete_confirm = st.checkbox(
            "ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÑƒÑŽ Ð¿Ð¾Ð²Ð½Ðµ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð½Ñ Ñ†Ñ–Ñ”Ñ— Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ð· Ð±Ð°Ð·Ð¸",
            key=f"{key_prefix}_delete_confirm_{publication_id}",
        )
        if st.button(
            "Ð’Ð¸Ð´Ð°Ð»Ð¸Ñ‚Ð¸ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑŽ Ð· Ð±Ð°Ð·Ð¸",
            key=f"{key_prefix}_delete_button_{publication_id}",
            use_container_width=True,
            type="primary",
        ):
            if not delete_confirm:
                st.warning("Ð¡Ð¿Ð¾Ñ‡Ð°Ñ‚ÐºÑƒ Ð¿Ñ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ñ–Ñ‚ÑŒ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð½Ñ Ð·Ð°Ð¿Ð¸ÑÑƒ.")
            elif service.delete_publication(publication_id):
                st.session_state[PUBLICATION_FLASH_KEY] = "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑŽ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð¾ Ð· Ð±Ð°Ð·Ð¸."
                st.rerun()
            else:
                st.error("ÐÐµ Ð²Ð´Ð°Ð»Ð¾ÑÑ Ð²Ð¸Ð´Ð°Ð»Ð¸Ñ‚Ð¸ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑŽ. Ð¡Ð¿Ñ€Ð¾Ð±ÑƒÐ¹Ñ‚Ðµ Ñ‰Ðµ Ñ€Ð°Ð·.")


def _render_publication_details(selected_publication: dict[str, object]) -> None:
    render_key_value_card(
        "ÐšÐ¾Ñ€Ð¾Ñ‚ÐºÐ° Ñ–Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ñ–Ñ",
        [
            ("ÐÐ°Ð·Ð²Ð°", str(selected_publication.get("title") or "")),
            ("Ð Ñ–Ðº", str(selected_publication.get("year") or "Ð½/Ð´")),
            ("DOI", str(selected_publication.get("doi") or "ÐÐµÐ¼Ð°Ñ”")),
            ("Ð¢Ð¸Ð¿", str(selected_publication.get("pub_type") or "ÐÐµÐ²Ñ–Ð´Ð¾Ð¼Ð¾")),
            ("Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾", str(selected_publication.get("source") or "ÐÐµÐ²Ñ–Ð´Ð¾Ð¼Ð¾")),
            ("Ð¡Ñ‚Ð°Ñ‚ÑƒÑ", str(selected_publication.get("status") or "ÐÐµÐ²Ñ–Ð´Ð¾Ð¼Ð¾")),
            ("ÐšÑ–Ð»ÑŒÐºÑ–ÑÑ‚ÑŒ Ð°Ð²Ñ‚Ð¾Ñ€Ñ–Ð²", str(selected_publication.get("authors_count") or 0)),
        ],
    )
    render_key_value_card(
        "ÐÐ²Ñ‚Ð¾Ñ€ÑÑŒÐºÐ¸Ð¹ ÑÐºÐ»Ð°Ð´",
        [
            (
                "ÐÐ²Ñ‚Ð¾Ñ€Ð¸",
                ", ".join(str(author) for author in selected_publication.get("authors", []) if author) or "ÐÐµÐ¼Ð°Ñ” Ð´Ð°Ð½Ð¸Ñ…",
            ),
        ],
    )


if hasattr(st, "dialog"):
    @st.dialog("Ð Ð¾Ð±Ð¾Ñ‡Ð° Ð¿Ð°Ð½ÐµÐ»ÑŒ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹", width="large")
    def _publication_workspace_dialog(service, rows: list[dict[str, object]], all_teachers: list[dict[str, object]]) -> None:
        st.caption("Ð’ÐµÐ»Ð¸ÐºÐ° Ð¿Ð°Ð½ÐµÐ»ÑŒ Ð´Ð»Ñ Ð¼Ð°ÑÐ¾Ð²Ð¾Ð³Ð¾ Ð²Ñ–Ð´Ð±Ð¾Ñ€Ñƒ, Ð¼Ð¾Ð´ÐµÑ€Ð°Ñ†Ñ–Ñ— Ñ‚Ð° Ñ€ÐµÐ´Ð°Ð³ÑƒÐ²Ð°Ð½Ð½Ñ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹.")
        if not rows:
            render_empty_state("ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹ Ð½ÐµÐ¼Ð°Ñ”", "Ð”Ð»Ñ Ð¿Ð¾Ñ‚Ð¾Ñ‡Ð½Ð¾Ð³Ð¾ Ñ„Ñ–Ð»ÑŒÑ‚Ñ€Ð° Ð½ÐµÐ¼Ð°Ñ” Ð·Ð°Ð¿Ð¸ÑÑ–Ð², ÑÐºÑ– Ð¼Ð¾Ð¶Ð½Ð° Ð²Ñ–Ð´ÐºÑ€Ð¸Ñ‚Ð¸ Ð² Ð¿Ð°Ð½ÐµÐ»Ñ–.")
            return

        search = st.text_input(
            "ÐŸÐ¾ÑˆÑƒÐº ÑƒÑÐµÑ€ÐµÐ´Ð¸Ð½Ñ– Ð¿Ð°Ð½ÐµÐ»Ñ–",
            placeholder="ÐÐ°Ð·Ð²Ð°, DOI, Ð´Ð¶ÐµÑ€ÐµÐ»Ð¾ Ð°Ð±Ð¾ ÑÑ‚Ð°Ñ‚ÑƒÑ",
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
        if top_controls[0].button("ÐŸÐ¾Ð·Ð½Ð°Ñ‡Ð¸Ñ‚Ð¸ Ð²ÑÐµ Ð²Ð¸Ð´Ð¸Ð¼Ðµ", key="publication_workspace_select_all", use_container_width=True):
            st.session_state["publication_workspace_selection"] = list(option_map.keys())
            st.rerun()
        if top_controls[1].button("ÐžÑ‡Ð¸ÑÑ‚Ð¸Ñ‚Ð¸ Ð²Ð¸Ð±Ñ–Ñ€", key="publication_workspace_clear", use_container_width=True):
            st.session_state["publication_workspace_selection"] = []
            st.rerun()
        top_controls[2].caption(f"Ð£ ÑÐ¿Ð¸ÑÐºÑƒ: {len(visible_rows)} | ÐŸÐ¾Ð·Ð½Ð°Ñ‡ÐµÐ½Ð¾: {len(current_selection)}")

        selected_labels = st.multiselect(
            "Ð’Ð¸Ð±Ñ–Ñ€ Ð·Ð°Ð¿Ð¸ÑÑ–Ð²",
            list(option_map.keys()),
            default=current_selection,
            key="publication_workspace_selection",
            placeholder="ÐŸÐ¾Ð·Ð½Ð°Ñ‡Ñ‚Ðµ ÐºÐ¾Ð½ÐºÑ€ÐµÑ‚Ð½Ñ– Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ð°Ð±Ð¾ Ð²ÐµÑÑŒ Ð¿Ð¾Ñ‚Ð¾Ñ‡Ð½Ð¸Ð¹ Ð·Ñ€Ñ–Ð·",
        )
        selected_rows = [option_map[label] for label in selected_labels if label in option_map]

        workspace = st.columns([1.22, 0.78], gap="large")
        with workspace[0]:
            render_adaptive_dataframe(publications_dataframe_admin(visible_rows), use_container_width=True, hide_index=True, height=520)

        with workspace[1]:
            if len(selected_rows) == 1:
                _render_publication_editor(service, selected_rows[0], all_teachers, key_prefix="workspace_publication")
            elif len(selected_rows) > 1:
                _render_bulk_workspace_actions(service, selected_rows, key_prefix="workspace_bulk")
            else:
                render_empty_state(
                    "ÐÐµÐ¼Ð°Ñ” Ð²Ð¸Ð±Ð¾Ñ€Ñƒ",
                    "ÐžÐ±ÐµÑ€Ñ–Ñ‚ÑŒ Ð¾Ð´Ð½Ñƒ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑŽ Ð´Ð»Ñ Ð´ÐµÑ‚Ð°Ð»ÑŒÐ½Ð¾Ð³Ð¾ Ñ€ÐµÐ´Ð°Ð³ÑƒÐ²Ð°Ð½Ð½Ñ Ð°Ð±Ð¾ ÐºÑ–Ð»ÑŒÐºÐ° Ð´Ð»Ñ Ð¼Ð°ÑÐ¾Ð²Ð¾Ñ— Ð´Ñ–Ñ—.",
                )
else:
    def _publication_workspace_dialog(service, rows: list[dict[str, object]], all_teachers: list[dict[str, object]]) -> None:
        del service, rows, all_teachers
        st.info("Ð”Ð»Ñ Ñ†ÑŒÐ¾Ð³Ð¾ ÑÐµÑ€ÐµÐ´Ð¾Ð²Ð¸Ñ‰Ð° Ð¿Ð¾Ð²Ð½Ð° Ð¿Ð°Ð½ÐµÐ»ÑŒ Ð½ÐµÐ´Ð¾ÑÑ‚ÑƒÐ¿Ð½Ð°. Ð¡ÐºÐ¾Ñ€Ð¸ÑÑ‚Ð°Ð¹Ñ‚ÐµÑÑ ÑÑ‚Ð°Ð½Ð´Ð°Ñ€Ñ‚Ð½Ð¸Ð¼ Ð±Ð»Ð¾ÐºÐ¾Ð¼ Ð´ÐµÑ‚Ð°Ð»ÐµÐ¹ Ð¿Ñ€Ð°Ð²Ð¾Ñ€ÑƒÑ‡.")


def render() -> None:
    service = require_service()
    admin_mode = is_admin_mode()
    render_header("ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—", "ÐšÐ°Ñ‚Ð°Ð»Ð¾Ð³ Ð½Ð°ÑƒÐºÐ¾Ð²Ð¸Ñ… Ñ€Ð¾Ð±Ñ–Ñ‚ Ð· Ñ„Ñ–Ð»ÑŒÑ‚Ñ€Ð°Ð¼Ð¸, Ð´ÐµÑ‚Ð°Ð»ÑÐ¼Ð¸ Ð·Ð°Ð¿Ð¸ÑÑ–Ð² Ñ– Ð¿Ñ€Ð¸Ð²'ÑÐ·ÐºÐ¾ÑŽ Ð´Ð¾ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð².")
    _show_flash_message()

    years = service.get_publication_years()
    year_options = ["Ð£ÑÑ– Ñ€Ð¾ÐºÐ¸"] + [str(year) for year in years]

    all_teachers = service.get_teachers()
    teacher_name_to_department = {
        str(row.get("full_name") or "").strip(): {
            "department_code": str(row.get("department_code") or "").strip(),
            "department_name": str(row.get("department_name") or "").strip(),
        }
        for row in all_teachers
    }
    department_options = {"Ð£ÑÑ– ÐºÐ°Ñ„ÐµÐ´Ñ€Ð¸": ""}
    for row in all_teachers:
        department_code = str(row.get("department_code") or "").strip()
        department_name = str(row.get("department_name") or "").strip()
        if department_code and department_name:
            department_options[f"{department_name} ({department_code})"] = department_code
    teacher_options = {"Ð£ÑÑ– Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–": ""}
    for row in all_teachers:
        teacher_options[str(row.get("full_name") or "").strip()] = str(row.get("full_name") or "").strip()

    filter_rows_top = st.columns(3, gap="large")
    selected_year = filter_rows_top[0].selectbox("Ð¤Ñ–Ð»ÑŒÑ‚Ñ€ Ð·Ð° Ñ€Ð¾ÐºÐ¾Ð¼", year_options)
    year_value = None if selected_year == "Ð£ÑÑ– Ñ€Ð¾ÐºÐ¸" else int(selected_year)
    search_query = filter_rows_top[1].text_input("ÐŸÐ¾ÑˆÑƒÐº Ð·Ð° Ð½Ð°Ð·Ð²Ð¾ÑŽ Ð°Ð±Ð¾ DOI", placeholder="Ð’Ð²ÐµÐ´Ñ–Ñ‚ÑŒ Ð½Ð°Ð·Ð²Ñƒ, DOI Ð°Ð±Ð¾ Ñ„Ñ€Ð°Ð³Ð¼ÐµÐ½Ñ‚ Ð´Ð¶ÐµÑ€ÐµÐ»Ð°").strip().lower()
    selected_teacher_name = filter_rows_top[2].selectbox("Ð¤Ñ–Ð»ÑŒÑ‚Ñ€ Ð·Ð° Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡ÐµÐ¼", list(teacher_options.keys()))

    publication_rows = service.get_publications(year=year_value)
    status_counts = _status_counts(publication_rows)
    available_statuses = [status for status in STATUS_ORDER if status_counts[status] > 0]
    source_counts = _source_counts(publication_rows)

    filter_rows_bottom = st.columns(4, gap="large")
    selected_department_label = filter_rows_bottom[0].selectbox("Ð¤Ñ–Ð»ÑŒÑ‚Ñ€ Ð·Ð° ÐºÐ°Ñ„ÐµÐ´Ñ€Ð¾ÑŽ", list(department_options.keys()))
    selected_department_code = department_options[selected_department_label]
    selected_status = filter_rows_bottom[1].selectbox("Ð¡Ñ‚Ð°Ñ‚ÑƒÑ Ñ€Ð¾Ð±Ñ–Ñ‚", ["Ð£ÑÑ– ÑÑ‚Ð°Ñ‚ÑƒÑÐ¸"] + available_statuses)
    selected_source = filter_rows_bottom[2].selectbox("Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾", ["Ð£ÑÑ– Ð´Ð¶ÐµÑ€ÐµÐ»Ð°"] + sorted(source_counts.keys()))
    only_coauthored = filter_rows_bottom[3].checkbox("Ð›Ð¸ÑˆÐµ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ð·Ñ– ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€Ð°Ð¼Ð¸")

    filtered_rows = publication_rows
    if search_query:
        filtered_rows = [
            row
            for row in filtered_rows
            if search_query in str(row.get("title", "")).lower()
            or search_query in str(row.get("doi", "")).lower()
            or search_query in str(row.get("source", "")).lower()
        ]
    if selected_teacher_name != "Ð£ÑÑ– Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–":
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
    if selected_status != "Ð£ÑÑ– ÑÑ‚Ð°Ñ‚ÑƒÑÐ¸":
        filtered_rows = [row for row in filtered_rows if row.get("status") == selected_status]
    if selected_source != "Ð£ÑÑ– Ð´Ð¶ÐµÑ€ÐµÐ»Ð°":
        filtered_rows = [
            row
            for row in filtered_rows
            if (str(row.get("source") or "").strip() or "ÐÐµÐ²Ñ–Ð´Ð¾Ð¼Ð¾") == selected_source
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
            "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹ Ð½Ðµ Ð·Ð½Ð°Ð¹Ð´ÐµÐ½Ð¾",
            "Ð—Ð¼Ñ–Ð½Ñ–Ñ‚ÑŒ Ñ„Ñ–Ð»ÑŒÑ‚Ñ€Ð¸ Ð°Ð±Ð¾ Ð¿Ð¾ÑÐ»Ð°Ð±Ñ‚Ðµ Ð¿Ð¾ÑˆÑƒÐº, Ñ‰Ð¾Ð± Ð¿ÐµÑ€ÐµÐ³Ð»ÑÐ½ÑƒÑ‚Ð¸ Ð´Ð¾ÑÑ‚ÑƒÐ¿Ð½Ñ– Ñ€Ð¾Ð±Ð¾Ñ‚Ð¸.",
        )
        return

    filtered_status_counts = _status_counts(filtered_rows)
    publications_count = len(filtered_rows)
    authorship_links = sum(int(row.get("authors_count", 0) or 0) for row in filtered_rows)
    covered_years = len({row.get("year") for row in filtered_rows if row.get("year") is not None})

    metrics = st.columns(4, gap="medium")
    with metrics[0]:
        render_summary_strip("ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—", str(publications_count))
    with metrics[1]:
        render_summary_strip(
            "ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ñ–",
            str(filtered_status_counts["ÐžÑ„Ñ–Ñ†Ñ–Ð¹Ð½Ð¾ Ð¿Ñ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾"] + filtered_status_counts["ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾"]),
        )
    with metrics[2]:
        render_summary_strip("ÐŸÐ¾Ñ‚Ñ€ÐµÐ±ÑƒÑŽÑ‚ÑŒ Ð¿ÐµÑ€ÐµÐ²Ñ–Ñ€ÐºÐ¸", str(filtered_status_counts["ÐŸÐ¾Ñ‚Ñ€ÐµÐ±ÑƒÑ” Ð¿ÐµÑ€ÐµÐ²Ñ–Ñ€ÐºÐ¸"]))
    with metrics[3]:
        render_summary_strip("ÐžÑ…Ð¾Ð¿Ð»ÐµÐ½Ñ– Ñ€Ð¾ÐºÐ¸", str(covered_years))

    secondary = st.columns(3, gap="medium")
    secondary[0].metric("ÐÐ²Ñ‚Ð¾Ñ€ÑÑŒÐºÑ– Ð²Ñ…Ð¾Ð´Ð¶ÐµÐ½Ð½Ñ", authorship_links)
    secondary[1].metric("ÐšÐ°Ð½Ð´Ð¸Ð´Ð°Ñ‚Ð¸", filtered_status_counts["ÐšÐ°Ð½Ð´Ð¸Ð´Ð°Ñ‚"])
    secondary[2].metric("Ð¡Ð¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€ÑÑŒÐºÑ– Ñ€Ð¾Ð±Ð¾Ñ‚Ð¸", sum(1 for row in filtered_rows if int(row.get("authors_count", 0) or 0) > 1))

    publication_map = {_publication_option(row): row for row in filtered_rows}

    layout = st.columns([1.16, 0.94], gap="large")
    with layout[0]:
        render_fullscreen_dataframe_heading(
            "Ð¢Ð°Ð±Ð»Ð¸Ñ†Ñ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹",
            publications_table,
            key="publications_table_fullscreen",
            subtitle="ÐÐ°Ñ‚Ð¸ÑÐ½Ñ–Ñ‚ÑŒ Ð½Ð° Ð·Ð°Ð³Ð¾Ð»Ð¾Ð²Ð¾Ðº, Ñ‰Ð¾Ð± Ð²Ñ–Ð´ÐºÑ€Ð¸Ñ‚Ð¸ Ð¿Ð¾Ð²Ð½Ð¸Ð¹ Ð¿ÐµÑ€ÐµÐ³Ð»ÑÐ´ Ñ‚Ð°Ð±Ð»Ð¸Ñ†Ñ–.",
            caption="ÐŸÐ¾Ð²Ð½Ð¸Ð¹ Ð·Ñ€Ñ–Ð· Ð²Ñ–Ð´Ñ„Ñ–Ð»ÑŒÑ‚Ñ€Ð¾Ð²Ð°Ð½Ð¸Ñ… Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹.",
        )
        controls = st.columns([0.64, 0.36], gap="small")
        if admin_mode:
            if controls[0].button("Ð’Ñ–Ð´ÐºÑ€Ð¸Ñ‚Ð¸ Ñ€Ð¾Ð±Ð¾Ñ‡Ñƒ Ð¿Ð°Ð½ÐµÐ»ÑŒ", use_container_width=True, key="open_publication_workspace"):
                _publication_workspace_dialog(service, filtered_rows, all_teachers)
        else:
            controls[0].caption("ÐŸÑƒÐ±Ð»Ñ–Ñ‡Ð½Ð¸Ð¹ Ñ€ÐµÐ¶Ð¸Ð¼: Ð¼Ð¾Ð´ÐµÑ€Ð°Ñ†Ñ–Ñ Ñ‚Ð° Ñ€ÐµÐ´Ð°Ð³ÑƒÐ²Ð°Ð½Ð½Ñ Ð¿Ñ€Ð¸Ñ…Ð¾Ð²Ð°Ð½Ñ–.")
        controls[1].download_button(
            "Ð•ÐºÑÐ¿Ð¾Ñ€Ñ‚ Ð¿Ð¾Ñ‚Ð¾Ñ‡Ð½Ð¾Ð³Ð¾ Ð·Ñ€Ñ–Ð·Ñƒ CSV",
            _csv_bytes(publications_table),
            file_name="publications_current_slice.csv",
            mime="text/csv",
            use_container_width=True,
        )
        publications_preview = _build_publications_preview_frame(publications_table, admin_mode=admin_mode)
        render_adaptive_dataframe(publications_preview, use_container_width=True, hide_index=True, height=300)

    with layout[1]:
        render_section_heading("Ð”ÐµÑ‚Ð°Ð»Ñ– Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—")
        selected_publication_label = st.selectbox("ÐžÐ±Ñ€Ð°Ñ‚Ð¸ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑŽ", list(publication_map.keys()))
        selected_publication = publication_map[selected_publication_label]
        if admin_mode:
            _render_publication_editor(service, selected_publication, all_teachers, key_prefix="publication")
        else:
            _render_publication_details(selected_publication)
