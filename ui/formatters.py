from __future__ import annotations

import pandas as pd


def _frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows or [])


def _join_authors(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item)
    return str(value or "")


def _format_confidence(value: object) -> str:
    try:
        return f"{float(value or 0):.2f}"
    except Exception:
        return "0.00"


def department_overview_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "code": "Код кафедри",
            "name": "Кафедра",
            "faculty_code": "Код факультету",
            "faculty_name": "Факультет",
            "teachers": "Викладачі",
            "publications": "Публікації",
        }
    )
    return renamed[["Код кафедри", "Кафедра", "Факультет", "Викладачі", "Публікації"]]


def faculty_overview_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "code": "Код факультету",
            "name": "Факультет",
            "departments": "Кафедри",
            "teachers": "Викладачі",
            "publications": "Публікації",
        }
    )
    return renamed[["Код факультету", "Факультет", "Кафедри", "Викладачі", "Публікації"]]


def teachers_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "id": "ID",
            "full_name": "ПІБ",
            "position": "Посада",
            "academic_degree": "Науковий ступінь",
            "academic_title": "Вчене звання",
            "department_name": "Кафедра",
            "faculty_name": "Факультет",
            "publications": "Публікації",
        }
    )
    return renamed[["ID", "ПІБ", "Посада", "Науковий ступінь", "Вчене звання", "Кафедра", "Факультет", "Публікації"]]


def teacher_publications_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    df["authors"] = df["authors"].apply(_join_authors)
    if "confidence" in df.columns:
        df["confidence"] = df["confidence"].apply(_format_confidence)
    renamed = df.rename(
        columns={
            "id": "ID",
            "title": "Публікація",
            "status": "Статус",
            "confidence": "Рівень довіри",
            "year": "Рік",
            "doi": "DOI",
            "pub_type": "Тип",
            "source": "Джерело",
            "authors": "Автори",
        }
    )
    columns = ["ID", "Публікація", "Статус", "Рівень довіри", "Рік", "DOI", "Тип", "Джерело", "Автори"]
    return renamed[columns]


def coauthors_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    df["publication_examples"] = df["publication_examples"].apply(_join_authors)
    renamed = df.rename(
        columns={
            "full_name": "Співавтор",
            "shared_publications": "Спільні публікації",
            "publication_examples": "Приклади публікацій",
        }
    )
    return renamed[["Співавтор", "Спільні публікації", "Приклади публікацій"]]


def publications_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    df["authors"] = df["authors"].apply(_join_authors)
    if "confidence" in df.columns:
        df["confidence"] = df["confidence"].apply(_format_confidence)
    renamed = df.rename(
        columns={
            "id": "ID",
            "title": "Назва",
            "status": "Статус",
            "confidence": "Рівень довіри",
            "year": "Рік",
            "doi": "DOI",
            "pub_type": "Тип",
            "source": "Джерело",
            "authors": "Автори",
            "authors_count": "Кількість авторів",
        }
    )
    columns = ["ID", "Назва", "Статус", "Рівень довіри", "Рік", "DOI", "Тип", "Джерело", "Кількість авторів", "Автори"]
    return renamed[columns]


def graph_edges_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "teacher_name": "Викладач",
            "department_name": "Кафедра",
            "publication_title": "Публікація",
            "year": "Рік",
        }
    )
    return renamed[["Викладач", "Кафедра", "Публікація", "Рік"]]


def top_teachers_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "teacher": "Викладач",
            "department": "Кафедра",
            "publications": "Кількість публікацій",
        }
    )
    return renamed[["Викладач", "Кафедра", "Кількість публікацій"]]


def top_coauthor_pairs_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    df["sample_publications"] = df["sample_publications"].apply(_join_authors)
    renamed = df.rename(
        columns={
            "teacher_a": "Викладач 1",
            "teacher_b": "Викладач 2",
            "shared_publications": "Спільні публікації",
            "sample_publications": "Приклади",
        }
    )
    return renamed[["Викладач 1", "Викладач 2", "Спільні публікації", "Приклади"]]


def centrality_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "teacher": "Викладач",
            "connections": "Кількість зв'язків",
            "weighted_connections": "Зважені зв'язки",
            "degree_centrality": "Degree centrality",
            "betweenness_centrality": "Betweenness centrality",
        }
    )
    return renamed[
        [
            "Викладач",
            "Кількість зв'язків",
            "Зважені зв'язки",
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
            "source": "Джерело",
            "publications": "Публікації",
        }
    )
    return renamed[["Джерело", "Публікації"]]


def audit_events_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = _frame(rows)
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "created_at": "Час",
            "action": "Дія",
            "entity_type": "Сутність",
            "entity_id": "ID сутності",
            "summary": "Опис",
            "details": "Деталі",
            "actor": "Ініціатор",
        }
    )
    return renamed[["Час", "Дія", "Сутність", "ID сутності", "Опис", "Деталі", "Ініціатор"]]
