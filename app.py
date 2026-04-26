from __future__ import annotations

import streamlit as st

from ui.components import require_service, setup_page
from ui.sidebar import render_sidebar
from views import analytics, dashboard, data_center, graph, publications, structure, teachers


PAGES: dict[str, dict[str, object]] = {
    "dashboard": {"title": "Дашборд", "section": "Огляд", "render": dashboard.render},
    "graph": {"title": "Граф", "section": "Огляд", "render": graph.render},
    "analytics": {"title": "Аналітика", "section": "Огляд", "render": analytics.render},
    "structure": {"title": "Структура", "section": "Каталог", "render": structure.render},
    "teachers": {"title": "Викладачі", "section": "Каталог", "render": teachers.render},
    "publications": {"title": "Публікації", "section": "Каталог", "render": publications.render},
    "data-center": {"title": "Центр даних", "section": "Адміністрування", "render": data_center.render},
}

DEFAULT_PAGE = "dashboard"


def _resolve_current_page() -> str:
    raw_query_page = str(st.query_params.get("page", "") or "").strip()
    session_page = str(st.session_state.get("current_page", "") or "").strip()

    if raw_query_page in PAGES:
        page = raw_query_page
    elif session_page in PAGES:
        page = session_page
    else:
        page = DEFAULT_PAGE

    st.session_state["current_page"] = page
    st.query_params["page"] = page
    return page


setup_page("Академічна мережа KSPU")
service = require_service()
current_page = _resolve_current_page()
selected_page = render_sidebar(service, current_page=current_page, pages=PAGES)

if selected_page != current_page:
    st.session_state["current_page"] = selected_page
    st.query_params["page"] = selected_page
    st.rerun()

page_render = PAGES[current_page]["render"]
page_render()
