from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from typing import Any


OPENALEX_API = "https://api.openalex.org/works"


def _get_json(url: str, timeout: int = 20) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "kspu-neo4j-publication-import/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_doi(doi: str | None) -> str:
    if not doi:
        return ""
    value = doi.strip()
    value = value.replace("https://doi.org/", "")
    value = value.replace("http://doi.org/", "")
    return value.lower()


def clean_title(title: str | None) -> str:
    return re.sub(r"\s+", " ", title or "").strip()


def title_case_name(value: str | None) -> str:
    if not value:
        return ""

    parts = re.split(r"(\s+|-)", value.strip().lower())
    fixed = []

    for part in parts:
        if part.isspace() or part == "-":
            fixed.append(part)
        elif part:
            fixed.append(part[:1].upper() + part[1:])

    return "".join(fixed)


def normalize_person_name(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower().replace("’", "'").replace("ʼ", "'")
    value = re.sub(r"[^a-zа-яіїєґё\s'-]", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def split_name(value: str | None) -> list[str]:
    normalized = normalize_person_name(value)
    return [part for part in re.split(r"\s+", normalized) if part]


def author_matches_teacher(author_name: str, teacher_name: str) -> bool:
    """
    Более строгая проверка, чтобы не цеплять чужих однофамильцев из OpenAlex.

    Для украинских/русских ФИО обычно нужно:
    - совпадение фамилии;
    - плюс совпадение имени или инициалов.
    """
    teacher_parts = split_name(teacher_name)
    author_parts = split_name(author_name)

    if not teacher_parts or not author_parts:
        return False

    teacher_surname = teacher_parts[0]
    teacher_given = teacher_parts[1] if len(teacher_parts) > 1 else ""

    author_joined = " ".join(author_parts)

    surname_ok = teacher_surname in author_parts or teacher_surname in author_joined
    if not surname_ok:
        return False

    if not teacher_given:
        return True

    given_ok = teacher_given in author_parts or teacher_given[:1] in [part[:1] for part in author_parts if part]

    return given_ok


def make_publication_id(title: str, year: int | None, doi: str = "", openalex_id: str = "") -> str:
    if doi:
        return f"doi:{normalize_doi(doi)}"

    if openalex_id:
        return f"openalex:{openalex_id.rsplit('/', 1)[-1]}"

    raw = f"{title}|{year or ''}".lower().strip()
    return "pub:" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def search_openalex_publications(
    teacher_name: str,
    from_year: int | None = None,
    per_page: int = 10,
) -> list[dict[str, Any]]:
    teacher_name = title_case_name(teacher_name)

    params = {
        "search": teacher_name,
        "per-page": str(per_page),
        "sort": "publication_year:desc",
    }

    if from_year:
        params["filter"] = f"from_publication_date:{from_year}-01-01"

    query = urllib.parse.urlencode(params)
    url = f"{OPENALEX_API}?{query}"

    data = _get_json(url)
    results = data.get("results", [])

    publications: list[dict[str, Any]] = []

    for item in results:
        title = clean_title(item.get("title"))
        if not title:
            continue

        authorships = item.get("authorships") or []
        authors = []

        for authorship in authorships:
            author = authorship.get("author") or {}
            display_name = title_case_name(author.get("display_name"))
            if display_name:
                authors.append(display_name)

        if not any(author_matches_teacher(author, teacher_name) for author in authors):
            continue

        year = item.get("publication_year")
        doi = normalize_doi(item.get("doi"))
        openalex_id = item.get("id", "")

        source = ""
        primary_location = item.get("primary_location") or {}
        source_obj = primary_location.get("source") or {}

        if source_obj:
            source = source_obj.get("display_name") or ""

        pub_type = item.get("type") or item.get("type_crossref") or ""

        publications.append(
            {
                "id": make_publication_id(title, year, doi=doi, openalex_id=openalex_id),
                "title": title,
                "year": int(year) if year else None,
                "doi": doi,
                "openalex_id": openalex_id,
                "source": source or "OpenAlex",
                "pub_type": pub_type,
                "authors": authors,
                "external_url": item.get("id", ""),
                "cited_by_count": int(item.get("cited_by_count") or 0),
            }
        )

    return publications
