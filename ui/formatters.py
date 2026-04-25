from __future__ import annotations

import pandas as pd


def _frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows or [])


def _join_authors(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item)
    return str(value or "")


def department_overview_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "code": "ÐšÐ¾Ð´ ÐºÐ°Ñ„ÐµÐ´Ñ€Ð¸",
            "name": "ÐšÐ°Ñ„ÐµÐ´Ñ€Ð°",
            "faculty_code": "ÐšÐ¾Ð´ Ñ„Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚Ñƒ",
            "faculty_name": "Ð¤Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚",
            "teachers": "Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–",
            "publications": "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—",
        }
    )
    return renamed[["ÐšÐ¾Ð´ ÐºÐ°Ñ„ÐµÐ´Ñ€Ð¸", "ÐšÐ°Ñ„ÐµÐ´Ñ€Ð°", "Ð¤Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚", "Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–", "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—"]]


def faculty_overview_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "code": "ÐšÐ¾Ð´ Ñ„Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚Ñƒ",
            "name": "Ð¤Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚",
            "departments": "ÐšÐ°Ñ„ÐµÐ´Ñ€Ð¸",
            "teachers": "Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–",
            "publications": "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—",
        }
    )
    return renamed[["ÐšÐ¾Ð´ Ñ„Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚Ñƒ", "Ð¤Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚", "ÐšÐ°Ñ„ÐµÐ´Ñ€Ð¸", "Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡Ñ–", "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—"]]


def teachers_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "id": "ID",
            "full_name": "ÐŸÐ†Ð‘",
            "position": "ÐŸÐ¾ÑÐ°Ð´Ð°",
            "academic_degree": "ÐÐ°ÑƒÐºÐ¾Ð²Ð¸Ð¹ ÑÑ‚ÑƒÐ¿Ñ–Ð½ÑŒ",
            "academic_title": "Ð’Ñ‡ÐµÐ½Ðµ Ð·Ð²Ð°Ð½Ð½Ñ",
            "department_name": "ÐšÐ°Ñ„ÐµÐ´Ñ€Ð°",
            "faculty_name": "Ð¤Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚",
            "publications": "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—",
        }
    )
    return renamed[["ID", "ÐŸÐ†Ð‘", "ÐŸÐ¾ÑÐ°Ð´Ð°", "ÐÐ°ÑƒÐºÐ¾Ð²Ð¸Ð¹ ÑÑ‚ÑƒÐ¿Ñ–Ð½ÑŒ", "Ð’Ñ‡ÐµÐ½Ðµ Ð·Ð²Ð°Ð½Ð½Ñ", "ÐšÐ°Ñ„ÐµÐ´Ñ€Ð°", "Ð¤Ð°ÐºÑƒÐ»ÑŒÑ‚ÐµÑ‚", "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—"]]


def teacher_publications_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    df["authors"] = df["authors"].apply(_join_authors)
    renamed = df.rename(
        columns={
            "id": "ID",
            "title": "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ",
            "year": "Ð Ñ–Ðº",
            "doi": "DOI",
            "pub_type": "Ð¢Ð¸Ð¿",
            "source": "Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾",
            "authors": "ÐÐ²Ñ‚Ð¾Ñ€Ð¸",
        }
    )
    return renamed[["ID", "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ", "Ð Ñ–Ðº", "DOI", "Ð¢Ð¸Ð¿", "Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾", "ÐÐ²Ñ‚Ð¾Ñ€Ð¸"]]


def coauthors_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    df["publication_examples"] = df["publication_examples"].apply(_join_authors)
    renamed = df.rename(
        columns={
            "full_name": "Ð¡Ð¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€",
            "shared_publications": "Ð¡Ð¿Ñ–Ð»ÑŒÐ½Ñ– Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—",
            "publication_examples": "ÐŸÑ€Ð¸ÐºÐ»Ð°Ð´Ð¸ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹",
        }
    )
    return renamed[["Ð¡Ð¿Ñ–Ð²Ð°Ð²Ñ‚Ð¾Ñ€", "Ð¡Ð¿Ñ–Ð»ÑŒÐ½Ñ– Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—", "ÐŸÑ€Ð¸ÐºÐ»Ð°Ð´Ð¸ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹"]]


def publications_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    df["authors"] = df["authors"].apply(_join_authors)
    renamed = df.rename(
        columns={
            "id": "ID",
            "title": "ÐÐ°Ð·Ð²Ð°",
            "year": "Ð Ñ–Ðº",
            "doi": "DOI",
            "pub_type": "Ð¢Ð¸Ð¿",
            "source": "Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾",
            "authors": "ÐÐ²Ñ‚Ð¾Ñ€Ð¸",
            "authors_count": "ÐšÑ–Ð»ÑŒÐºÑ–ÑÑ‚ÑŒ Ð°Ð²Ñ‚Ð¾Ñ€Ñ–Ð²",
        }
    )
    return renamed[["ID", "ÐÐ°Ð·Ð²Ð°", "Ð Ñ–Ðº", "DOI", "Ð¢Ð¸Ð¿", "Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾", "ÐšÑ–Ð»ÑŒÐºÑ–ÑÑ‚ÑŒ Ð°Ð²Ñ‚Ð¾Ñ€Ñ–Ð²", "ÐÐ²Ñ‚Ð¾Ñ€Ð¸"]]


def graph_edges_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "teacher_name": "Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡",
            "department_name": "ÐšÐ°Ñ„ÐµÐ´Ñ€Ð°",
            "publication_title": "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ",
            "year": "Ð Ñ–Ðº",
        }
    )
    return renamed[["Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡", "ÐšÐ°Ñ„ÐµÐ´Ñ€Ð°", "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ", "Ð Ñ–Ðº"]]


def top_teachers_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "teacher": "Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡",
            "department": "ÐšÐ°Ñ„ÐµÐ´Ñ€Ð°",
            "publications": "ÐšÑ–Ð»ÑŒÐºÑ–ÑÑ‚ÑŒ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹",
        }
    )
    return renamed[["Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡", "ÐšÐ°Ñ„ÐµÐ´Ñ€Ð°", "ÐšÑ–Ð»ÑŒÐºÑ–ÑÑ‚ÑŒ Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ð¹"]]


def top_coauthor_pairs_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    df["sample_publications"] = df["sample_publications"].apply(_join_authors)
    renamed = df.rename(
        columns={
            "teacher_a": "Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡ 1",
            "teacher_b": "Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡ 2",
            "shared_publications": "Ð¡Ð¿Ñ–Ð»ÑŒÐ½Ñ– Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—",
            "sample_publications": "ÐŸÑ€Ð¸ÐºÐ»Ð°Ð´Ð¸",
        }
    )
    return renamed[["Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡ 1", "Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡ 2", "Ð¡Ð¿Ñ–Ð»ÑŒÐ½Ñ– Ð¿ÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—", "ÐŸÑ€Ð¸ÐºÐ»Ð°Ð´Ð¸"]]


def centrality_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "teacher": "Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡",
            "connections": "ÐšÑ–Ð»ÑŒÐºÑ–ÑÑ‚ÑŒ Ð·Ð²'ÑÐ·ÐºÑ–Ð²",
            "weighted_connections": "Ð—Ð²Ð°Ð¶ÐµÐ½Ñ– Ð·Ð²'ÑÐ·ÐºÐ¸",
            "degree_centrality": "Degree centrality",
            "betweenness_centrality": "Betweenness centrality",
        }
    )
    return renamed[
        [
            "Ð’Ð¸ÐºÐ»Ð°Ð´Ð°Ñ‡",
            "ÐšÑ–Ð»ÑŒÐºÑ–ÑÑ‚ÑŒ Ð·Ð²'ÑÐ·ÐºÑ–Ð²",
            "Ð—Ð²Ð°Ð¶ÐµÐ½Ñ– Ð·Ð²'ÑÐ·ÐºÐ¸",
            "Degree centrality",
            "Betweenness centrality",
        ]
    ]


def publication_sources_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "source": "Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾",
            "publications": "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—",
        }
    )
    return renamed[["Ð”Ð¶ÐµÑ€ÐµÐ»Ð¾", "ÐŸÑƒÐ±Ð»Ñ–ÐºÐ°Ñ†Ñ–Ñ—"]]
