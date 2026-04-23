from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
import streamlit as st


load_dotenv()


@dataclass(frozen=True)
class Neo4jConfig:
    uri: str
    user: str
    password: str
    database: str = "neo4j"


def _read_streamlit_secret(key: str) -> str:
    try:
        value = st.secrets[key]
    except Exception:
        return ""
    return str(value).strip()


def get_neo4j_config() -> Neo4jConfig | None:
    uri = _read_streamlit_secret("NEO4J_URI") or os.getenv("NEO4J_URI", "").strip()
    user = _read_streamlit_secret("NEO4J_USER") or os.getenv("NEO4J_USER", "").strip()
    password = _read_streamlit_secret("NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD", "").strip()
    database = _read_streamlit_secret("NEO4J_DATABASE") or os.getenv("NEO4J_DATABASE", "neo4j").strip()

    if not (uri and user and password):
        return None

    return Neo4jConfig(uri=uri, user=user, password=password, database=database or "neo4j")


def get_connection_help_text() -> str:
    return (
        "??? Streamlit Cloud ??????? ????????? ??????????? ?? Neo4j Aura ????? `Secrets`.\n"
        "???????? ????? ??????????????? `st.secrets` ??? `.env`:\n\n"
        "`NEO4J_URI`\n"
        "`NEO4J_USER`\n"
        "`NEO4J_PASSWORD`\n"
        "`NEO4J_DATABASE` (??????'??????, ?????? `neo4j`)"
    )
