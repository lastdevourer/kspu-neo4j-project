from __future__ import annotations

import hashlib
import re
from typing import Any

from scholarly import scholarly


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def stable_publication_id(title: str, year: int | None) -> str:
    raw = f"{clean_text(title).lower()}|{year or ''}"
    return "pub:" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def title_case_name(value: str | None) -> str:
    value = clean_text(value)
    if not value:
        return ""

    parts = re.split(r"(\s+|-)", value.lower())
    result = []

    for part in parts:
        if part.isspace() or part == "-":
            result.append(part)
        elif part:
            result.append(part[:1].upper() + part[1:])

    return "".join(result)


def scholar_author_id_from_url(url: str) -> str:
    match = re.search(r"[?&]user=([^&]+)", url or "")
    return match.group(1) if match else ""


def split_authors(authors_raw: Any) -> list[str]:
    if isinstance(authors_raw, list):
        return [title_case_name(author) for author in authors_raw if author]

    if not isinstance(authors_raw, str):
        return []

    parts = re.split(r"\s+and\s+|,\s*", authors_raw)
    return [title_case_name(part) for part in parts if clean_text(part)]


def load_publications_from_scholar_id(scholar_id: str, limit: int = 50) -> list[dict[str, Any]]:
    if not scholar_id:
        return []

    try:
        author = scholarly.search_author_id(scholar_id)
        filled_author = scholarly.fill(author, sections=["publications"])
    except Exception:
        return []

    publications = []

    for pub in filled_author.get("publications", [])[:limit]:
        try:
            filled_pub = scholarly.fill(pub)
        except Exception:
            filled_pub = pub

        bib = filled_pub.get("bib", {}) or {}

        title = clean_text(bib.get("title"))
        if not title:
            continue

        year_raw = bib.get("pub_year") or bib.get("year")
        try:
            year = int(year_raw) if year_raw else None
        except Exception:
            year = None

        authors = split_authors(bib.get("author", ""))

        publications.append(
            {
                "id": stable_publication_id(title, year),
                "title": title,
                "year": year,
                "doi": "",
                "openalex_id": "",
                "source": "Google Scholar",
                "pub_type": "scholarly publication",
                "authors": authors,
                "external_url": filled_pub.get("pub_url", ""),
                "cited_by_count": int(filled_pub.get("num_citations") or 0),
            }
        )

    return publications
