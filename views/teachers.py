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
from ui.formatters import (
    coauthors_dataframe,
    teacher_publications_dataframe_admin,
    teacher_publications_dataframe_public,
    teachers_dataframe_admin,
    teachers_dataframe_public,
)


STATUS_ORDER = [
    "ÐžÑ„Ñ–Ñ†Ñ–Ð¹Ð½Ð¾ Ð¿Ñ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾",
    "ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾",
    "ÐšÐ°Ð½Ð´Ð¸Ð´Ð°Ñ‚",
    "ÐŸÐ¾Ñ‚Ñ€ÐµÐ±ÑƒÑ” Ð¿ÐµÑ€ÐµÐ²Ñ–Ñ€ÐºÐ¸",
    "Ð’Ñ–Ð´Ñ…Ð¸Ð»ÐµÐ½Ð¾",
    "Ð’ Ñ‡Ð¾Ñ€Ð½Ð¾Ð¼Ñƒ ÑÐ¿Ð¸ÑÐºÑƒ",
]

TEACHER_FLASH_KEY = "teacher_management_flash"


def _csv_bytes(frame):
    return frame.to_csv(index=False).encode("utf-8-sig")


def _profile_count(profile: dict[str, object]) -> int:
    return sum(
        1
        for key in ("orcid", "google_scholar", "scopus", "web_of_science")
        if str(profile.get(key) or "").strip()
    )


def _profile_readiness(profile: dict[str, object], publications: list[dict[str, object]]) -> tuple[str, str]:
    profile_count = _profile_count(profile)
    publications_count = len(publications)
    official_count = sum(1 for row in publications if row.get("status") == "ÐžÑ„Ñ–Ñ†Ñ–Ð¹Ð½Ð¾ Ð¿Ñ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾")

    if profile_count >= 3 and (publications_count >= 5 or official_count >= 1):
        return "Ð’Ð¸ÑÐ¾ÐºÐ°", "ÐŸÑ€Ð¾Ñ„Ñ–Ð»ÑŒ Ð´Ð¾Ð±Ñ€Ðµ Ð¿Ñ–Ð´Ð³Ð¾Ñ‚Ð¾Ð²Ð»ÐµÐ½Ð¸Ð¹ Ð´Ð¾ Ð°Ð²Ñ‚Ð¾Ð¼Ð°Ñ‚Ð¸Ñ‡Ð½Ð¾Ð³Ð¾ Ñ–Ð¼Ð¿Ð¾Ñ€Ñ‚Ñƒ Ñ‚Ð° Ð¿ÐµÑ€ÐµÐ²Ñ–Ñ€ÐºÐ¸."
    if profile_count >= 2 and publications_count >= 1:
        return "Ð¡ÐµÑ€ÐµÐ´Ð½Ñ", "Ð„ ÐºÑ–Ð»ÑŒÐºÐ° Ð·Ð¾Ð²Ð½Ñ–ÑˆÐ½Ñ–Ñ… Ð¿Ñ€Ð¾Ñ„Ñ–Ð»Ñ–Ð² Ñ– Ð²Ð¶Ðµ Ð·Ð½Ð°Ð¹Ð´ÐµÐ½Ñ– Ñ€Ð¾Ð±Ð¾Ñ‚Ð¸."
    if profile_count >= 1:
        return "Ð‘Ð°Ð·Ð¾Ð²Ð°", "ÐŸÐ¾Ñ‡Ð°Ñ‚ÐºÐ¾Ð²Ñ– Ñ–Ð´ÐµÐ½Ñ‚Ð¸Ñ„Ñ–ÐºÐ°Ñ‚Ð¾Ñ€Ð¸ Ñ”, Ð°Ð»Ðµ Ð²Ð°Ñ€Ñ‚Ð¾ Ñ€Ð¾Ð·ÑˆÐ¸Ñ€Ð¸Ñ‚Ð¸ Ð¿Ð¾ÐºÑ€Ð¸Ñ‚Ñ‚Ñ Ð´Ð¶ÐµÑ€ÐµÐ»."
    return "ÐÐ¸Ð·ÑŒÐºÐ°", "ÐŸÑ€Ð¾Ñ„Ñ–Ð»ÑŒ Ñ‰Ðµ Ð¿Ð¾Ñ‚Ñ€ÐµÐ±ÑƒÑ” ORCID, Scopus, WoS Ð°Ð±Ð¾ Scholar Ð´Ð»Ñ ÐºÑ€Ð°Ñ‰Ð¾Ð³Ð¾ Ð¼Ð°Ñ‚Ñ‡Ñ–Ð½Ð³Ñƒ."


def _profile_status(value: str) -> str:
    return value if value else "ÐÐµÐ¼Ð°Ñ”"


def _sync_caption(profile: dict[str, object]) -> str:
    synced_at = str(profile.get("last_publication_sync_at") or "").strip()
    trigger = str(profile.get("last_publication_sync_trigger") or "").strip()
    status = str(profile.get("last_publication_sync_status") or "").strip()
    if not synced_at:
        return "Ð©Ðµ Ð½Ðµ Ð·Ð°Ð¿ÑƒÑÐºÐ°Ð»Ð¾ÑÑ"

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


def _show_flash_message() -> None:
    message = st.session_state.pop(TEACHER_FLASH_KEY, "")
    if message:
        st.success(message)


def _build_teacher_publications_preview(frame, *, admin_mode: bool):
    preview_columns = (
        ["ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ", "Ð¡Ñ‚Ð°Ñ‚ÑƒÑ", "Ð Ñ–Ðº", "Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾"]
        if not admin_mode
        else ["ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ", "Ð¡Ñ‚Ð°Ñ‚ÑƒÑ", "Ð Ñ–Ð²ÐµÐ½ÑŒ Ð´Ð¾Ð²Ñ–Ñ€Ð¸", "Ð Ñ–Ðº", "Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾"]
    )
    existing_columns = [column for column in preview_columns if column in frame.columns]
    return frame[existing_columns].copy() if existing_columns else frame


def _publication_option(row: dict[str, object]) -> str:
    year = row.get("year")
    year_label = str(year) if year is not None else "Ð½/Ð´"
    status = str(row.get("status") or "")
    return f"{row.get('title', 'Ð‘ÐµÐ· Ð½Ð°Ð·Ð²Ð¸')} ({year_label}) | {status}"


def _render_publication_management(
    service,
    teacher_id: str,
    publications: list[dict[str, object]],
    all_publications: list[dict[str, object]],
) -> None:
    with st.expander("ÐšÐµÑ€ÑƒÐ²Ð°Ð½Ð½Ñ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑÐ¼Ð¸", expanded=False):
        linked_ids = {str(row.get("id") or "").strip() for row in publications if row.get("id")}
        candidate_search = st.text_input(
            "Ð—Ð½Ð°Ð¹Ñ‚Ð¸ Ð½Ð°ÑÐ²Ð½Ñƒ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑŽ Ð´Ð»Ñ Ð¿Ñ€Ð¸Ð²'ÑÐ·ÑƒÐ²Ð°Ð½Ð½Ñ",
            placeholder="Ð’Ð²ÐµÐ´Ñ–Ñ‚ÑŒ Ð½Ð°Ð·Ð²Ñƒ Ð°Ð±Ð¾ DOI",
            key=f"teacher_link_search_{teacher_id}",
        ).strip().lower()
        available_publications = [
            row
            for row in all_publications
            if str(row.get("id") or "").strip() not in linked_ids
            and (
                not candidate_search
                or candidate_search in str(row.get("title") or "").lower()
                or candidate_search in str(row.get("doi") or "").lower()
            )
        ]
        available_map = {_publication_option(row): row for row in available_publications[:120]}
        link_columns = st.columns([1.2, 0.8], gap="medium")
        if available_map:
            selected_candidate_label = link_columns[0].selectbox(
                "Ð”Ð¾Ð´Ð°Ñ‚Ð¸ Ð½Ð°ÑÐ²Ð½Ñƒ Ñ€Ð¾Ð±Ð¾Ñ‚Ñƒ",
                list(available_map.keys()),
                key=f"teacher_link_publication_{teacher_id}",
            )
            selected_candidate = available_map[selected_candidate_label]
            if link_columns[1].button(
                "ÐŸÑ€Ð¸Ð²'ÑÐ·Ð°Ñ‚Ð¸ Ð´Ð¾ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°",
                key=f"teacher_link_button_{teacher_id}",
                use_container_width=True,
            ):
                candidate_id = str(selected_candidate.get("id") or "").strip()
                if service.create_teacher_publication_link(teacher_id, candidate_id):
                    st.session_state[TEACHER_FLASH_KEY] = "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑŽ Ð¿Ñ€Ð¸Ð²'ÑÐ·Ð°Ð½Ð¾ Ð´Ð¾ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°."
                    st.rerun()
                st.error("ÐÐµ Ð²Ð´Ð°Ð»Ð¾ÑÑ ÑÑ‚Ð²Ð¾Ñ€Ð¸Ñ‚Ð¸ Ð·Ð²'ÑÐ·Ð¾Ðº. Ð¡Ð¿Ñ€Ð¾Ð±ÑƒÐ¹Ñ‚Ðµ Ñ‰Ðµ Ñ€Ð°Ð·.")
        else:
            st.caption("Ð”Ð»Ñ Ñ†ÑŒÐ¾Ð³Ð¾ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð° Ð½Ðµ Ð·Ð½Ð°Ð¹Ð´ÐµÐ½Ð¾ Ð´Ð¾Ð´Ð°Ñ‚ÐºÐ¾Ð²Ð¸Ñ… Ð½Ð°ÑÐ²Ð½Ð¸Ñ… Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹ Ð·Ð° Ð¿Ð¾Ñ‚Ð¾Ñ‡Ð½Ð¸Ð¼ Ñ„Ñ–Ð»ÑŒÑ‚Ñ€Ð¾Ð¼.")

        if not publications:
            return

        publication_map = {_publication_option(row): row for row in publications}
        selected_label = st.selectbox(
            "Ð—Ð°Ð¿Ð¸Ñ Ð´Ð»Ñ Ñ€ÐµÐ´Ð°Ð³ÑƒÐ²Ð°Ð½Ð½Ñ",
            list(publication_map.keys()),
            key=f"teacher_publication_manage_{teacher_id}",
        )
        selected_publication = publication_map[selected_label]
        publication_id = str(selected_publication.get("id") or "").strip()
        details = service.get_publication_management_details(publication_id) or {}

        render_key_value_card(
            "Ð’Ð¿Ð»Ð¸Ð² Ð½Ð° Ð±Ð°Ð·Ñƒ",
            [
                ("ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ", str(details.get("title") or selected_publication.get("title") or "")),
                ("Ð Ñ–Ðº", str(details.get("year") or selected_publication.get("year") or "Ð½/Ð´")),
                ("Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾", str(details.get("source") or selected_publication.get("source") or "ÐÐµÐ²Ñ–Ð´Ð¾Ð¼Ð¾")),
                ("ÐŸÐ¾Ð²'ÑÐ·Ð°Ð½Ñ– Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–", str(details.get("linked_teachers_count") or 0)),
            ],
        )

        linked_teachers = details.get("linked_teachers") or []
        if linked_teachers:
            st.caption("Ð—Ð°Ð¿Ð¸Ñ Ð·Ð°Ñ€Ð°Ð· Ð¿Ñ€Ð¸Ð²'ÑÐ·Ð°Ð½Ð¸Ð¹ Ð´Ð¾: " + ", ".join(str(item) for item in linked_teachers if item))

        review_note = st.text_area(
            "ÐÐ¾Ñ‚Ð°Ñ‚ÐºÐ° Ð¼Ð¾Ð´ÐµÑ€Ð°Ñ‚Ð¾Ñ€Ð°",
            value=str(details.get("review_note") or selected_publication.get("review_note") or ""),
            height=90,
            key=f"teacher_review_note_{teacher_id}_{publication_id}",
        )

        status_actions = st.columns(2, gap="medium")
        if status_actions[0].button(
            "ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¸Ñ‚Ð¸ Ð·Ð°Ð¿Ð¸Ñ",
            key=f"teacher_confirm_{teacher_id}_{publication_id}",
            use_container_width=True,
        ):
            if service.set_publication_review_status(publication_id, "ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾", review_note=review_note):
                st.session_state[TEACHER_FLASH_KEY] = "Ð¡Ñ‚Ð°Ñ‚ÑƒÑ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ð¾Ð½Ð¾Ð²Ð»ÐµÐ½Ð¾."
                st.rerun()
        if status_actions[1].button(
            "Ð’Ñ–Ð´Ñ…Ð¸Ð»Ð¸Ñ‚Ð¸ Ð·Ð°Ð¿Ð¸Ñ",
            key=f"teacher_reject_{teacher_id}_{publication_id}",
            use_container_width=True,
        ):
            if service.set_publication_review_status(publication_id, "Ð’Ñ–Ð´Ñ…Ð¸Ð»ÐµÐ½Ð¾", review_note=review_note):
                st.session_state[TEACHER_FLASH_KEY] = "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑŽ Ð²Ñ–Ð´Ñ…Ð¸Ð»ÐµÐ½Ð¾."
                st.rerun()

        detach_confirm = st.checkbox(
            "ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÑƒÑŽ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð½Ñ Ð·Ð²'ÑÐ·ÐºÑƒ Ñ†Ñ–Ñ”Ñ— Ñ€Ð¾Ð±Ð¾Ñ‚Ð¸ Ð· Ð¿Ð¾Ñ‚Ð¾Ñ‡Ð½Ð¸Ð¼ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡ÐµÐ¼",
            key=f"detach_confirm_{teacher_id}_{publication_id}",
        )
        delete_confirm = st.checkbox(
            "ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÑƒÑŽ Ð¿Ð¾Ð²Ð½Ðµ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð½Ñ Ñ†Ñ–Ñ”Ñ— Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ð· Ð±Ð°Ð·Ð¸",
            key=f"delete_confirm_{teacher_id}_{publication_id}",
        )

        actions = st.columns(2, gap="medium")
        if actions[0].button(
            "Ð’Ð¸Ð´Ð°Ð»Ð¸Ñ‚Ð¸ Ð·Ð²'ÑÐ·Ð¾Ðº Ð· Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡ÐµÐ¼",
            key=f"detach_button_{teacher_id}_{publication_id}",
            use_container_width=True,
        ):
            if not detach_confirm:
                st.warning("Ð¡Ð¿Ð¾Ñ‡Ð°Ñ‚ÐºÑƒ Ð¿Ñ–Ð´Ñ‚Ð²ÐµÑ€Ð´ÑŒÑ‚Ðµ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð½Ñ Ð·Ð²'ÑÐ·ÐºÑƒ.")
            elif service.delete_teacher_publication_link(teacher_id, publication_id):
                st.session_state[TEACHER_FLASH_KEY] = "Ð—Ð²'ÑÐ·Ð¾Ðº Ð°Ð²Ñ‚Ð¾Ñ€Ð° Ð· Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ”ÑŽ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð¾."
                st.rerun()
            else:
                st.error("ÐÐµ Ð²Ð´Ð°Ð»Ð¾ÑÑ Ð²Ð¸Ð´Ð°Ð»Ð¸Ñ‚Ð¸ Ð·Ð²'ÑÐ·Ð¾Ðº. Ð¡Ð¿Ñ€Ð¾Ð±ÑƒÐ¹Ñ‚Ðµ Ñ‰Ðµ Ñ€Ð°Ð·.")

        if actions[1].button(
            "Ð’Ð¸Ð´Ð°Ð»Ð¸Ñ‚Ð¸ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑŽ Ð¿Ð¾Ð²Ð½Ñ–ÑÑ‚ÑŽ",
            key=f"delete_button_{teacher_id}_{publication_id}",
            use_container_width=True,
            type="primary",
        ):
            if not delete_confirm:
                st.warning("Ð¡Ð¿Ð¾Ñ‡Ð°Ñ‚ÐºÑƒ Ð¿Ñ–Ð´Ñ‚Ð²ÐµÑ€Ð´ÑŒÑ‚Ðµ Ð¿Ð¾Ð²Ð½Ðµ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð½Ñ Ð·Ð°Ð¿Ð¸ÑÑƒ.")
            elif service.delete_publication(publication_id):
                st.session_state[TEACHER_FLASH_KEY] = "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑŽ Ð¿Ð¾Ð²Ð½Ñ–ÑÑ‚ÑŽ Ð²Ð¸Ð´Ð°Ð»ÐµÐ½Ð¾ Ð· Ð±Ð°Ð·Ð¸."
                st.rerun()
            else:
                st.error("ÐÐµ Ð²Ð´Ð°Ð»Ð¾ÑÑ Ð²Ð¸Ð´Ð°Ð»Ð¸Ñ‚Ð¸ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–ÑŽ. Ð¡Ð¿Ñ€Ð¾Ð±ÑƒÐ¹Ñ‚Ðµ Ñ‰Ðµ Ñ€Ð°Ð·.")


def render() -> None:
    service = require_service()
    admin_mode = is_admin_mode()
    render_header("Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–", "ÐŸÐ¾ÑˆÑƒÐº, Ð¿Ñ€Ð¾Ñ„Ñ–Ð»Ñ–, Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ñ‚Ð° ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€ÑÑŒÐºÑ– Ð·Ð²'ÑÐ·ÐºÐ¸ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð² ÑƒÐ½Ñ–Ð²ÐµÑ€ÑÐ¸Ñ‚ÐµÑ‚Ñƒ.")
    _show_flash_message()

    departments = service.get_departments()
    department_labels = {"Ð£ÑÑ– ÐºÐ°Ñ„ÐµÐ´Ñ€Ð¸": ""}
    for row in departments:
        department_labels[f"{row['name']} ({row['code']})"] = row["code"]

    filters = st.columns([1.45, 1.05], gap="large")
    search_value = filters[0].text_input("ÐŸÐ¾ÑˆÑƒÐº Ð·Ð° ÐŸÐ†Ð‘", placeholder="Ð’Ð²ÐµÐ´Ñ–Ñ‚ÑŒ Ð¿Ñ€Ñ–Ð·Ð²Ð¸Ñ‰Ðµ Ð°Ð±Ð¾ Ñ‡Ð°ÑÑ‚Ð¸Ð½Ñƒ Ñ–Ð¼ÐµÐ½Ñ–")
    selected_department_label = filters[1].selectbox("Ð¤Ñ–Ð»ÑŒÑ‚Ñ€ Ð·Ð° ÐºÐ°Ñ„ÐµÐ´Ñ€Ð¾ÑŽ", list(department_labels.keys()))
    selected_department_code = department_labels[selected_department_label]

    teacher_rows = service.get_teachers(search=search_value, department_code=selected_department_code)
    teachers_table = teachers_dataframe_admin(teacher_rows) if admin_mode else teachers_dataframe_public(teacher_rows)

    if teachers_table.empty:
        render_empty_state(
            "Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð² Ð½Ðµ Ð·Ð½Ð°Ð¹Ð´ÐµÐ½Ð¾",
            "Ð¡Ð¿Ñ€Ð¾Ð±ÑƒÐ¹Ñ‚Ðµ Ð·Ð¼Ñ–Ð½Ð¸Ñ‚Ð¸ Ð¿Ð¾ÑˆÑƒÐº Ð°Ð±Ð¾ Ð¿Ð¾ÑÐ»Ð°Ð±Ð¸Ñ‚Ð¸ Ñ„Ñ–Ð»ÑŒÑ‚Ñ€ Ð·Ð° ÐºÐ°Ñ„ÐµÐ´Ñ€Ð¾ÑŽ.",
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
        render_summary_strip("Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ– Ñƒ Ð²Ð¸Ð±Ñ–Ñ€Ñ†Ñ–", str(teacher_count))
    with metrics[1]:
        render_summary_strip("ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ñƒ Ð²Ð¸Ð±Ñ–Ñ€Ñ†Ñ–", str(publications_count))
    with metrics[2]:
        render_summary_strip("ÐŸÑ€Ð¾Ñ„Ñ–Ð»Ñ– Ð´Ð»Ñ Ñ–Ð¼Ð¿Ð¾Ñ€Ñ‚Ñƒ", str(ready_profiles_count), "Ð„ Ñ…Ð¾Ñ‡Ð° Ð± Ð¾Ð´Ð¸Ð½ Ð·Ð¾Ð²Ð½Ñ–ÑˆÐ½Ñ–Ð¹ Ñ–Ð´ÐµÐ½Ñ‚Ð¸Ñ„Ñ–ÐºÐ°Ñ‚Ð¾Ñ€.")
    with metrics[3]:
        render_summary_strip("ÐšÐ°Ñ„ÐµÐ´Ñ€Ð¸ Ñƒ Ð²Ð¸Ð±Ñ–Ñ€Ñ†Ñ–", str(departments_count))

    teacher_labels = {f"{row['full_name']} | {row['department_name']}": row["id"] for row in teacher_rows}
    selected_teacher_key = "teachers_selected_label"
    if teacher_labels:
        current_default = next(iter(teacher_labels.keys()))
        current_value = st.session_state.get(selected_teacher_key)
        if current_value not in teacher_labels:
            st.session_state[selected_teacher_key] = current_default
    selected_teacher_label = st.session_state[selected_teacher_key]
    selected_teacher_id = teacher_labels[selected_teacher_label]
    profile = service.get_teacher_profile(selected_teacher_id)
    if profile is None:
        render_empty_state(
            "ÐŸÑ€Ð¾Ñ„Ñ–Ð»ÑŒ Ñ‚Ð¸Ð¼Ñ‡Ð°ÑÐ¾Ð²Ð¾ Ð½ÐµÐ´Ð¾ÑÑ‚ÑƒÐ¿Ð½Ð¸Ð¹",
            "ÐÐµ Ð²Ð´Ð°Ð»Ð¾ÑÑ Ð·Ð½Ð°Ð¹Ñ‚Ð¸ Ð´ÐµÑ‚Ð°Ð»ÑŒÐ½Ñƒ ÐºÐ°Ñ€Ñ‚ÐºÑƒ Ñ†ÑŒÐ¾Ð³Ð¾ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°.",
        )
        return

    publications = service.get_teacher_publications(selected_teacher_id)
    all_publications = service.get_publications()
    coauthors = service.get_teacher_coauthors(selected_teacher_id)
    readiness_label, readiness_caption = _profile_readiness(profile, publications)
    status_counts = _status_counts(publications)

    layout = st.columns([1.1, 0.9], gap="large")

    with layout[0]:
        render_fullscreen_dataframe_heading(
            "Ð¢Ð°Ð±Ð»Ð¸Ñ†Ñ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð²",
            teachers_table,
            key="teachers_table_fullscreen",
            caption="ÐŸÐ¾Ð²Ð½Ð¸Ð¹ Ð¿ÐµÑ€ÐµÐ»Ñ–Ðº Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–Ð² Ñƒ Ð¿Ð¾Ñ‚Ð¾Ñ‡Ð½Ð¾Ð¼Ñƒ Ð·Ñ€Ñ–Ð·Ñ–.",
        )
        st.download_button(
            "Ð•ÐºÑÐ¿Ð¾Ñ€Ñ‚ Ð¿Ð¾Ñ‚Ð¾Ñ‡Ð½Ð¾Ð³Ð¾ Ð·Ñ€Ñ–Ð·Ñƒ CSV",
            _csv_bytes(teachers_table),
            file_name="teachers_current_slice.csv",
            mime="text/csv",
            use_container_width=True,
        )
        render_adaptive_dataframe(teachers_table, use_container_width=True, hide_index=True, height=320)

        lower_tabs = st.tabs(["ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°", "Ð¡Ð¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€Ð¸"])

        with lower_tabs[0]:
            available_statuses = [status for status in STATUS_ORDER if status_counts[status] > 0]
            publication_status_filter = st.selectbox(
                "ÐŸÐ¾ÐºÐ°Ð·Ð°Ñ‚Ð¸ ÑÑ‚Ð°Ñ‚ÑƒÑ",
                ["Ð£ÑÑ– ÑÑ‚Ð°Ñ‚ÑƒÑÐ¸"] + available_statuses,
                key="teacher_publication_status_filter",
            )
            filtered_publications = (
                publications
                if publication_status_filter == "Ð£ÑÑ– ÑÑ‚Ð°Ñ‚ÑƒÑÐ¸"
                else [row for row in publications if row.get("status") == publication_status_filter]
            )
            publications_table = (
                teacher_publications_dataframe_admin(filtered_publications)
                if admin_mode
                else teacher_publications_dataframe_public(filtered_publications)
            )
            if publications_table.empty:
                render_section_heading("ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°")
                render_empty_state(
                    "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹ Ð½Ðµ Ð·Ð½Ð°Ð¹Ð´ÐµÐ½Ð¾",
                    "Ð”Ð»Ñ Ñ†ÑŒÐ¾Ð³Ð¾ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð° Ñ‰Ðµ Ð½ÐµÐ¼Ð°Ñ” Ñ€Ð¾Ð±Ñ–Ñ‚ Ñƒ Ð²Ð¸Ð±Ñ€Ð°Ð½Ð¾Ð¼Ñƒ ÑÑ‚Ð°Ñ‚ÑƒÑÑ–.",
                )
            else:
                render_fullscreen_dataframe_heading(
                    "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ— Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°",
                    publications_table,
                    key=f"teacher_publications_fullscreen_{selected_teacher_id}",
                    caption="Ð Ð¾Ð·ÑˆÐ¸Ñ€ÐµÐ½Ð¸Ð¹ Ð¿ÐµÑ€ÐµÐ³Ð»ÑÐ´ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹ Ð²Ð¸Ð±Ñ€Ð°Ð½Ð¾Ð³Ð¾ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°.",
                )
                publications_preview = _build_teacher_publications_preview(publications_table, admin_mode=admin_mode)
                render_adaptive_dataframe(publications_preview, use_container_width=True, hide_index=True, height=260)

            if admin_mode:
                _render_publication_management(service, selected_teacher_id, publications, all_publications)

        with lower_tabs[1]:
            coauthors_table = coauthors_dataframe(coauthors)
            if coauthors_table.empty:
                render_section_heading("Ð¡Ð¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€Ð¸")
                render_empty_state(
                    "Ð¡Ð¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€Ñ–Ð² Ð½Ðµ Ð²Ð¸ÑÐ²Ð»ÐµÐ½Ð¾",
                    "Ð£ Ð¼ÐµÑ€ÐµÐ¶Ñ– Ñ‰Ðµ Ð½Ðµ Ð·Ð°Ñ„Ñ–ÐºÑÐ¾Ð²Ð°Ð½Ð¾ ÑÐ¿Ñ–Ð»ÑŒÐ½Ð¸Ñ… Ñ€Ð¾Ð±Ñ–Ñ‚ Ð· Ñ–Ð½ÑˆÐ¸Ð¼Ð¸ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°Ð¼Ð¸.",
                )
            else:
                render_fullscreen_dataframe_heading(
                    "Ð¡Ð¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€Ð¸ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°",
                    coauthors_table,
                    key=f"teacher_coauthors_fullscreen_{selected_teacher_id}",
                    caption="ÐŸÐ¾Ð²Ð½Ð¸Ð¹ ÑÐ¿Ð¸ÑÐ¾Ðº ÑÐ¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€Ñ–Ð² Ð²Ð¸Ð±Ñ€Ð°Ð½Ð¾Ð³Ð¾ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°.",
                )
                render_adaptive_dataframe(coauthors_table, use_container_width=True, hide_index=True, height=260)

    with layout[1]:
        render_section_heading("ÐšÐ°Ñ€Ñ‚ÐºÐ° Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°")
        st.selectbox("ÐžÐ±Ñ€Ð°Ñ‚Ð¸ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°", list(teacher_labels.keys()), key=selected_teacher_key)

        spotlight = st.columns(2, gap="medium")
        with spotlight[0]:
            render_summary_strip("Ð“Ð¾Ñ‚Ð¾Ð²Ð½Ñ–ÑÑ‚ÑŒ Ð¿Ñ€Ð¾Ñ„Ñ–Ð»ÑŽ", readiness_label, readiness_caption)
        with spotlight[1]:
            render_summary_strip("ÐžÑÑ‚Ð°Ð½Ð½Ñ” Ð¾Ð½Ð¾Ð²Ð»ÐµÐ½Ð½Ñ", _sync_caption(profile))

        counters = st.columns(4, gap="medium")
        counters[0].metric("ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—", len(publications))
        counters[1].metric("Ð¡Ð¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€Ð¸", len(coauthors))
        counters[2].metric(
            "ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ñ–",
            status_counts["ÐžÑ„Ñ–Ñ†Ñ–Ð¹Ð½Ð¾ Ð¿Ñ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾"] + status_counts["ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾"],
        )
        counters[3].metric("ÐšÐ°Ð½Ð´Ð¸Ð´Ð°Ñ‚Ð¸", status_counts["ÐšÐ°Ð½Ð´Ð¸Ð´Ð°Ñ‚"])

        passport_tab, profiles_tab, statuses_tab = st.tabs(["ÐŸÐ°ÑÐ¿Ð¾Ñ€Ñ‚", "ÐŸÑ€Ð¾Ñ„Ñ–Ð»Ñ–", "Ð¡Ñ‚Ð°Ñ‚ÑƒÑÐ¸"])

        with passport_tab:
            render_key_value_card(
                "ÐŸÐ°ÑÐ¿Ð¾Ñ€Ñ‚ Ð²Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ð°",
                [
                    ("ÐŸÐ†Ð‘", str(profile.get("full_name") or "")),
                    ("ÐšÐ°Ñ„ÐµÐ´Ñ€Ð°", str(profile.get("department_name") or "")),
                    ("Ð¤Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚", str(profile.get("faculty_name") or "")),
                    ("ÐŸÐ¾ÑÐ°Ð´Ð°", str(profile.get("position") or "")),
                    ("ÐÐ°ÑƒÐºÐ¾Ð²Ð¸Ð¹ ÑÑ‚ÑƒÐ¿Ñ–Ð½ÑŒ", str(profile.get("academic_degree") or "")),
                    ("Ð’Ñ‡ÐµÐ½Ðµ Ð·Ð²Ð°Ð½Ð½Ñ", str(profile.get("academic_title") or "")),
                ],
            )

        with profiles_tab:
            render_key_value_card(
                "Ð—Ð¾Ð²Ð½Ñ–ÑˆÐ½Ñ– Ð¿Ñ€Ð¾Ñ„Ñ–Ð»Ñ–",
                [
                    ("ORCID", _profile_status(str(profile.get("orcid") or "").strip())),
                    ("Google Scholar", _profile_status(str(profile.get("google_scholar") or "").strip())),
                    ("Scopus", _profile_status(str(profile.get("scopus") or "").strip())),
                    ("Web of Science", _profile_status(str(profile.get("web_of_science") or "").strip())),
                    ("ÐŸÑ€Ð¾Ñ„Ñ–Ð»ÑŒ KSU", _profile_status(str(profile.get("profile_url") or "").strip())),
                ],
            )

        with statuses_tab:
            render_key_value_card(
                "Ð¡Ñ‚Ð°Ñ‚ÑƒÑÐ¸ Ñ€Ð¾Ð±Ñ–Ñ‚",
                [
                    ("ÐžÑ„Ñ–Ñ†Ñ–Ð¹Ð½Ð¾ Ð¿Ñ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾", str(status_counts["ÐžÑ„Ñ–Ñ†Ñ–Ð¹Ð½Ð¾ Ð¿Ñ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾"])),
                    ("ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾", str(status_counts["ÐŸÑ–Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¶ÐµÐ½Ð¾"])),
                    ("ÐšÐ°Ð½Ð´Ð¸Ð´Ð°Ñ‚", str(status_counts["ÐšÐ°Ð½Ð´Ð¸Ð´Ð°Ñ‚"])),
                    ("ÐŸÐ¾Ñ‚Ñ€ÐµÐ±ÑƒÑ” Ð¿ÐµÑ€ÐµÐ²Ñ–Ñ€ÐºÐ¸", str(status_counts["ÐŸÐ¾Ñ‚Ñ€ÐµÐ±ÑƒÑ” Ð¿ÐµÑ€ÐµÐ²Ñ–Ñ€ÐºÐ¸"])),
                ],
            )
