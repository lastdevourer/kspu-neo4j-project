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
    database: str = ""


@dataclass(frozen=True)
class PublicationImportConfig:
    openalex_api_key: str = ""
    crossref_mailto: str = ""
    orcid_client_id: str = ""
    orcid_client_secret: str = ""
    scopus_api_key: str = ""
    scopus_insttoken: str = ""
    wos_api_key: str = ""
    max_works_per_teacher: int = 40


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
    database = _read_streamlit_secret("NEO4J_DATABASE") or os.getenv("NEO4J_DATABASE", "").strip()

    if not (uri and user and password):
        return None

    return Neo4jConfig(uri=uri, user=user, password=password, database=database)


def get_publication_import_config() -> PublicationImportConfig:
    max_works_value = _read_streamlit_secret("PUB_IMPORT_MAX_WORKS_PER_TEACHER") or os.getenv(
        "PUB_IMPORT_MAX_WORKS_PER_TEACHER",
        "",
    ).strip()
    try:
        max_works_per_teacher = max(5, min(int(max_works_value or "40"), 200))
    except ValueError:
        max_works_per_teacher = 40

    return PublicationImportConfig(
        openalex_api_key=_read_streamlit_secret("OPENALEX_API_KEY") or os.getenv("OPENALEX_API_KEY", "").strip(),
        crossref_mailto=_read_streamlit_secret("CROSSREF_MAILTO") or os.getenv("CROSSREF_MAILTO", "").strip(),
        orcid_client_id=_read_streamlit_secret("ORCID_CLIENT_ID") or os.getenv("ORCID_CLIENT_ID", "").strip(),
        orcid_client_secret=_read_streamlit_secret("ORCID_CLIENT_SECRET")
        or os.getenv("ORCID_CLIENT_SECRET", "").strip(),
        scopus_api_key=_read_streamlit_secret("SCOPUS_API_KEY") or os.getenv("SCOPUS_API_KEY", "").strip(),
        scopus_insttoken=_read_streamlit_secret("SCOPUS_INSTTOKEN") or os.getenv("SCOPUS_INSTTOKEN", "").strip(),
        wos_api_key=_read_streamlit_secret("WOS_API_KEY") or os.getenv("WOS_API_KEY", "").strip(),
        max_works_per_teacher=max_works_per_teacher,
    )


def get_connection_help_text() -> str:
    return (
        "Ð”Ð»Ñ Streamlit Cloud Ð´Ð¾Ð´Ð°Ð¹Ñ‚Ðµ Ð¿Ð°Ñ€Ð°Ð¼ÐµÑ‚Ñ€Ð¸ Ð¿Ñ–Ð´ÐºÐ»ÑŽÑ‡ÐµÐ½Ð½Ñ Ð´Ð¾ Neo4j Aura Ñ‡ÐµÑ€ÐµÐ· `Secrets`.\n"
        "Ð›Ð¾ÐºÐ°Ð»ÑŒÐ½Ð¾ Ð¼Ð¾Ð¶Ð½Ð° Ð²Ð¸ÐºÐ¾Ñ€Ð¸ÑÑ‚Ð¾Ð²ÑƒÐ²Ð°Ñ‚Ð¸ `st.secrets` Ð°Ð±Ð¾ `.env`:\n\n"
        "`NEO4J_URI`\n"
        "`NEO4J_USER`\n"
        "`NEO4J_PASSWORD`\n"
        "`NEO4J_DATABASE` (Ð½ÐµÐ¾Ð±Ð¾Ð²'ÑÐ·ÐºÐ¾Ð²Ð¾; ÑÐºÑ‰Ð¾ Ñ” Ð¿Ð¾Ð¼Ð¸Ð»ÐºÐ° Ð¼Ð°Ñ€ÑˆÑ€ÑƒÑ‚Ð¸Ð·Ð°Ñ†Ñ–Ñ—, ÐºÑ€Ð°Ñ‰Ðµ Ð¿Ñ€Ð¸Ð±Ñ€Ð°Ñ‚Ð¸ Ñ†ÐµÐ¹ Ð¿Ð°Ñ€Ð°Ð¼ÐµÑ‚Ñ€ Ñ– Ð´Ð°Ñ‚Ð¸ Aura "
        "Ð²Ð¸Ð±Ñ€Ð°Ñ‚Ð¸ Ð´Ð¾Ð¼Ð°ÑˆÐ½ÑŽ Ð±Ð°Ð·Ñƒ Ð°Ð²Ñ‚Ð¾Ð¼Ð°Ñ‚Ð¸Ñ‡Ð½Ð¾)"
    )
