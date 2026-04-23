import streamlit as st
import pandas as pd
from services.neo4j_service import Neo4jService
from ui.styles import apply_global_styles

apply_global_styles()

st.markdown("# 📈 Аналітика")

try:
    service = Neo4jService(
        uri=st.secrets["NEO4J_URI"],
        user=st.secrets["NEO4J_USERNAME"],
        password=st.secrets["NEO4J_PASSWORD"],
    )
    
    tab1, tab2, tab3 = st.tabs([
        "🏆 Топ викладачів",
        "📊 Статистика по кафедрах",
        "🤝 Найсильніші зв'язки"
    ])
    
    with tab1:
        st.markdown("## 🏆 Найпродуктивніші викладачі")
        
        limit = st.slider("Кількість записів:", 1, 50, 10)
        top_teachers = service.get_top_teachers(limit=limit)
        
        if top_teachers:
            df = pd.DataFrame(top_teachers)
            df.columns = ["ПІБ", "Публікацій"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.bar_chart(df.set_index("ПІБ"))
        else:
            st.info("Немає даних")
    
    with tab2:
        st.markdown("## 📊 Продуктивність кафедр")
        
        dept_stats = service.get_department_stats()
        
        if dept_stats:
            df = pd.DataFrame(dept_stats)
            df.columns = ["Код", "Кафедра", "Викладачів", "Публікацій"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.bar_chart(df.set_index("Кафедра")["Публікацій"])
        else:
            st.info("Немає даних")
    
    with tab3:
        st.markdown("## 🤝 Топ пари співавторів")
        
        limit = st.slider("Кількість пар:", 1, 50, 10, key="coauth_limit")
        coauth = service.get_coauthorships(limit=limit)
        
        if coauth:
            df = pd.DataFrame(coauth)
            df.columns = ["Автор 1", "Автор 2", "Спільних робіт"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.bar_chart(df.set_index("Автор 1")["Спільних робіт"]) 
        else:
            st.info("Немає даних")
    
    st.markdown("---")
    
    st.markdown("### 📌 Висновки")
    st.markdown("""
    - Ця аналітика допомагає виявити найбільш активних дослідників
    - Показує рівень співробітництва між викладачами
    - Дозволяє планувати розвиток наукових груп на кафедрах
    """)
    
    service.close()
    
except Exception as e:
    st.error(f"❌ Помилка: {e}")