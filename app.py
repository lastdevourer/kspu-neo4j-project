from __future__ import annotations

import streamlit as st

from ui.components import require_service, setup_page
from ui.sidebar import render_sidebar
from views import analytics, dashboard, data_center, graph, publications, structure, teachers


setup_page("Академічна мережа КСПУ / ХДУ")
service = require_service()
render_sidebar(service)

navigation = st.navigation(
    {
        "Огляд": [
            st.Page(dashboard.render, title="Дашборд", url_path="dashboard", default=True),
            st.Page(graph.render, title="Граф", url_path="graph"),
            st.Page(analytics.render, title="Аналітика", url_path="analytics"),
        ],
        "Каталог": [
            st.Page(structure.render, title="Структура", url_path="structure"),
            st.Page(teachers.render, title="Викладачі", url_path="teachers"),
            st.Page(publications.render, title="Публікації", url_path="publications"),
        ],
        "Адміністрування": [
            st.Page(data_center.render, title="Центр даних", url_path="data-center"),
        ],
    },
    position="sidebar",
    expanded=False,
)
navigation.run()
