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
    renamed = df.rename(
        columns={
            "id": "ID",
            "title": "Публікація",
            "year": "Рік",
            "doi": "DOI",
            "pub_type": "Тип",
            "source": "Джерело",
            "authors": "Автори",
        }
    )
    return renamed[["ID", "Публікація", "Рік", "DOI", "Тип", "Джерело", "Автори"]]


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
    renamed = df.rename(
        columns={
            "id": "ID",
            "title": "Назва",
            "year": "Рік",
            "doi": "DOI",
            "pub_type": "Тип",
            "source": "Джерело",
            "authors": "Автори",
            "authors_count": "Кількість авторів",
        }
    )
    return renamed[["ID", "Назва", "Рік", "DOI", "Тип", "Джерело", "Кількість авторів", "Автори"]]


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
