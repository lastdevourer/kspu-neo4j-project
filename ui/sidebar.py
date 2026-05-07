from __future__ import annotations

import streamlit as st

from config import get_admin_password, get_ui_theme, is_admin_mode


def render_sidebar(
    *,
    current_page: str,
    pages: dict[str, dict[str, object]],
) -> str:
    selected_page = current_page
    section_order = ["ÐžÐ³Ð»ÑÐ´", "ÐšÐ°Ñ‚Ð°Ð»Ð¾Ð³", "ÐÐ´Ð¼Ñ–Ð½Ñ–ÑÑ‚Ñ€ÑƒÐ²Ð°Ð½Ð½Ñ"]
    admin_password = get_admin_password()

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-kicker">KSU</div>
                <div class="sidebar-brand-title">ÐÐºÐ°Ð´ÐµÐ¼Ñ–Ñ‡Ð½Ð° Ð¼ÐµÑ€ÐµÐ¶Ð°</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        current_theme = get_ui_theme()
        st.markdown("**Ð¢ÐµÐ¼Ð° Ñ–Ð½Ñ‚ÐµÑ€Ñ„ÐµÐ¹ÑÑƒ**")
        theme_cols = st.columns([0.66, 0.34], gap="small")
        current_theme_label = "Ð¡Ð²Ñ–Ñ‚Ð»Ð° Ñ‚ÐµÐ¼Ð°" if current_theme == "light" else "Ð¢ÐµÐ¼Ð½Ð° Ñ‚ÐµÐ¼Ð°"
        theme_button_label = "â˜€ï¸ Ð¡Ð²Ñ–Ñ‚Ð»Ð°" if current_theme == "dark" else "ðŸŒ™ Ð¢ÐµÐ¼Ð½Ð°"
        theme_cols[0].markdown(
            f'<div class="sidebar-theme-caption">Ð—Ð°Ñ€Ð°Ð·: {current_theme_label}</div>',
            unsafe_allow_html=True,
        )
        if theme_cols[1].button(
            theme_button_label,
            key="sidebar_theme_toggle",
            use_container_width=True,
            help="ÐŸÐµÑ€ÐµÐ¼ÐºÐ½ÑƒÑ‚Ð¸ Ñ‚ÐµÐ¼Ñƒ Ñ–Ð½Ñ‚ÐµÑ€Ñ„ÐµÐ¹ÑÑƒ",
        ):
            next_theme = "light" if current_theme == "dark" else "dark"
            st.session_state["ui_theme"] = next_theme
            st.query_params["theme"] = next_theme
            st.rerun()

        for section_name in section_order:
            section_pages = [
                (page_key, page_meta)
                for page_key, page_meta in pages.items()
                if page_meta.get("section") == section_name
            ]
            if not section_pages:
                continue

            st.markdown(
                f'<div class="sidebar-section-label">{section_name}</div>',
                unsafe_allow_html=True,
            )
            for page_key, page_meta in section_pages:
                button_type = "primary" if page_key == current_page else "secondary"
                if st.button(
                    str(page_meta["title"]),
                    key=f"sidebar_nav_{page_key}",
                    use_container_width=True,
                    type=button_type,
                ):
                    selected_page = page_key

        if admin_password:
            st.markdown("---")
            st.markdown("**Ð ÐµÐ¶Ð¸Ð¼ ÐºÐµÑ€ÑƒÐ²Ð°Ð½Ð½Ñ**")
            if is_admin_mode():
                st.success("ÐÐ´Ð¼Ñ–Ð½Ñ€ÐµÐ¶Ð¸Ð¼ Ñ€Ð¾Ð·Ð±Ð»Ð¾ÐºÐ¾Ð²Ð°Ð½Ð¾ Ð´Ð»Ñ Ð¿Ð¾Ñ‚Ð¾Ñ‡Ð½Ð¾Ñ— ÑÐµÑÑ–Ñ—.")
                if st.button(
                    "Ð—Ð°ÐºÑ€Ð¸Ñ‚Ð¸ Ð°Ð´Ð¼Ñ–Ð½Ñ€ÐµÐ¶Ð¸Ð¼",
                    key="sidebar_lock_admin_mode",
                    use_container_width=True,
                ):
                    st.session_state["admin_unlocked"] = False
                    if current_page in {"structure", "data-center"}:
                        st.session_state["current_page"] = "dashboard"
                        st.query_params["page"] = "dashboard"
                        st.query_params["theme"] = get_ui_theme()
                    st.rerun()
            else:
                entered_password = st.text_input(
                    "ÐŸÐ°Ñ€Ð¾Ð»ÑŒ Ð°Ð´Ð¼Ñ–Ð½Ñ–ÑÑ‚Ñ€Ð°Ñ‚Ð¾Ñ€Ð°",
                    type="password",
                    key="sidebar_admin_password",
                    placeholder="Ð’Ð²ÐµÐ´Ñ–Ñ‚ÑŒ Ð¿Ð°Ñ€Ð¾Ð»ÑŒ Ð´Ð»Ñ Ñ€ÐµÐ´Ð°Ð³ÑƒÐ²Ð°Ð½Ð½Ñ",
                )
                if st.button(
                    "Ð Ð¾Ð·Ð±Ð»Ð¾ÐºÑƒÐ²Ð°Ñ‚Ð¸ Ð°Ð´Ð¼Ñ–Ð½Ñ€ÐµÐ¶Ð¸Ð¼",
                    key="sidebar_unlock_admin_mode",
                    use_container_width=True,
                ):
                    if entered_password == admin_password:
                        st.session_state["admin_unlocked"] = True
                        st.session_state.pop("sidebar_admin_password", None)
                        st.rerun()
                    st.error("ÐÐµÐ²Ñ–Ñ€Ð½Ð¸Ð¹ Ð¿Ð°Ñ€Ð¾Ð»ÑŒ Ð°Ð´Ð¼Ñ–Ð½Ñ–ÑÑ‚Ñ€Ð°Ñ‚Ð¾Ñ€Ð°.")

    return selected_page
