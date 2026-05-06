from __future__ import annotations

import streamlit as st

from config import get_admin_password, get_ui_theme, is_admin_mode


def render_sidebar(
    *,
    current_page: str,
    pages: dict[str, dict[str, object]],
) -> str:
    selected_page = current_page
    section_order = ["Огляд", "Каталог", "Адміністрування"]
    admin_password = get_admin_password()

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-kicker">KSU</div>
                <div class="sidebar-brand-title">Академічна мережа</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        current_theme = get_ui_theme()
        st.markdown("**Тема інтерфейсу**")
        theme_cols = st.columns([0.78, 0.22], gap="small")
        theme_label = "Світла тема" if current_theme == "light" else "Темна тема"
        theme_icon = "☀️" if current_theme == "dark" else "🌙"
        theme_cols[0].caption(f"Зараз: {theme_label}")
        if theme_cols[1].button(
            theme_icon,
            key="sidebar_theme_toggle",
            use_container_width=True,
            help="Перемкнути тему інтерфейсу",
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
            st.markdown("**Режим керування**")
            if is_admin_mode():
                st.success("Адмінрежим розблоковано для поточної сесії.")
                if st.button(
                    "Закрити адмінрежим",
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
                    "Пароль адміністратора",
                    type="password",
                    key="sidebar_admin_password",
                    placeholder="Введіть пароль для редагування",
                )
                if st.button(
                    "Розблокувати адмінрежим",
                    key="sidebar_unlock_admin_mode",
                    use_container_width=True,
                ):
                    if entered_password == admin_password:
                        st.session_state["admin_unlocked"] = True
                        st.session_state.pop("sidebar_admin_password", None)
                        st.rerun()
                    st.error("Невірний пароль адміністратора.")

    return selected_page
