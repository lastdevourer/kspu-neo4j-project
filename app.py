import streamlit as st
from neo4j import GraphDatabase

# подключение
URI = st.secrets["NEO4J_URI"]
USER = st.secrets["NEO4J_USER"]
PASSWORD = st.secrets["NEO4J_PASSWORD"]

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

st.title("KSPU Academic Graph")

# тест подключения
if st.button("Проверить подключение"):
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) AS cnt")
        count = result.single()["cnt"]
        st.success(f"Подключено! Узлов: {count}")