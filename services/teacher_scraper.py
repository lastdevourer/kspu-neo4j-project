import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}


DEPARTMENT_STAFF_URLS = {
    "D001": "https://www.kspu.edu/About/Faculty/FPhysMathemInformatics/ChairAlgGeomMathAnalysis/Staff.aspx",
    "D003": "https://www.kspu.edu/About/Faculty/FPhysMathemInformatics/ChairInformatics/Staff.aspx",
}


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding
    return resp.text


def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def extract_profile_links(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = clean_text(a.get_text(" ", strip=True))

        if not text:
            continue

        if len(text.split()) < 2:
            continue

        if not re.search(r"[А-ЯІЇЄҐ][а-яіїєґ'\-]+", text):
            continue

        full_url = urljoin("https://www.kspu.edu/", href)

        if "/Staff/" not in full_url:
            continue

        key = (text.lower(), full_url.lower())
        if key in seen:
            continue
        seen.add(key)

        rows.append({
            "full_name": text,
            "profile_url": full_url
        })

    return rows


def parse_profile(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    text = clean_text(soup.get_text(" ", strip=True))

    position = ""
    academic_degree = ""
    academic_title = ""
    orcid = ""
    google_scholar = ""
    scopus = ""

    pos_match = re.search(r"Посада[:\-]?\s*(.+?)(?=Науковий ступінь|Вчене звання|Робоча адреса|E-mail|Освіта)", text, re.IGNORECASE)
    if pos_match:
        position = clean_text(pos_match.group(1))

    deg_match = re.search(r"Науковий ступінь[:\-]?\s*(.+?)(?=Вчене звання|Робоча адреса|E-mail|Освіта)", text, re.IGNORECASE)
    if deg_match:
        academic_degree = clean_text(deg_match.group(1))

    title_match = re.search(r"Вчене звання[:\-]?\s*(.+?)(?=Робоча адреса|E-mail|Освіта)", text, re.IGNORECASE)
    if title_match:
        academic_title = clean_text(title_match.group(1))

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        label = clean_text(a.get_text(" ", strip=True)).lower()

        if "orcid.org" in href.lower() or "orcid" in label:
            orcid = href
        elif "scholar.google" in href.lower() or "google scholar" in label:
            google_scholar = href
        elif "scopus" in href.lower():
            scopus = href

    return {
        "position": position,
        "academic_degree": academic_degree,
        "academic_title": academic_title,
        "orcid": orcid,
        "google_scholar": google_scholar,
        "scopus": scopus,
    }


def scrape_department_teachers(department_id: str, faculty_id: str) -> list[dict]:
    if department_id not in DEPARTMENT_STAFF_URLS:
        return []

    staff_url = DEPARTMENT_STAFF_URLS[department_id]
    html = fetch_html(staff_url)
    people = extract_profile_links(html)

    results = []
    for idx, person in enumerate(people, start=1):
        try:
            profile_html = fetch_html(person["profile_url"])
            details = parse_profile(profile_html)
        except Exception:
            details = {
                "position": "",
                "academic_degree": "",
                "academic_title": "",
                "orcid": "",
                "google_scholar": "",
                "scopus": "",
            }

        results.append({
            "teacher_id": f"{department_id.replace('D', 'T')}{idx:03d}",
            "full_name": person["full_name"],
            "position": details["position"],
            "academic_degree": details["academic_degree"],
            "academic_title": details["academic_title"],
            "department_id": department_id,
            "faculty_id": faculty_id,
            "orcid": details["orcid"],
            "google_scholar": details["google_scholar"],
            "scopus": details["scopus"],
            "source_url": person["profile_url"],
        })

    return results
