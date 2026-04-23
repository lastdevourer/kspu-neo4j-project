import re
from urllib.parse import urljoin

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from neo4j import GraphDatabase

# =========================================================
# НАЛАШТУВАННЯ СТОРІНКИ
# =========================================================
st.set_page_config(page_title="Академічний граф ХДУ", layout="wide")
st.title("Академічний граф ХДУ")

# =========================================================
# ПЕРЕВІРКА SECRETS
# =========================================================
required_secrets = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]

for key in required_secrets:
    if key not in st.secrets:
        st.error(f"Додай {key} у Streamlit Secrets.")
        st.stop()

URI = st.secrets["NEO4J_URI"]
USER = st.secrets["NEO4J_USER"]
PASSWORD = st.secrets["NEO4J_PASSWORD"]

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


# =========================================================
# ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ NEO4J
# =========================================================
def run_query(query: str, params: dict | None = None):
    with driver.session() as session:
        result = session.run(query, params or {})
        return [dict(r) for r in result]


def execute_write(query: str, params: dict | None = None):
    with driver.session() as session:
        session.run(query, params or {})


def execute_many(query: str, rows: list[dict]):
    with driver.session() as session:
        session.run(query, {"rows": rows})


def create_constraints():
    queries = [
        "CREATE CONSTRAINT faculty_id_unique IF NOT EXISTS FOR (f:Faculty) REQUIRE f.faculty_id IS UNIQUE",
        "CREATE CONSTRAINT department_id_unique IF NOT EXISTS FOR (d:Department) REQUIRE d.department_id IS UNIQUE",
        "CREATE CONSTRAINT teacher_id_unique IF NOT EXISTS FOR (t:Teacher) REQUIRE t.teacher_id IS UNIQUE",
        "CREATE CONSTRAINT publication_id_unique IF NOT EXISTS FOR (p:Publication) REQUIRE p.publication_id IS UNIQUE",
        "CREATE CONSTRAINT topic_name_unique IF NOT EXISTS FOR (tp:Topic) REQUIRE tp.name IS UNIQUE",
    ]
    with driver.session() as session:
        for q in queries:
            session.run(q)


def get_counts():
    q = """
    CALL {
      MATCH (f:Faculty)
      RETURN count(f) AS faculties
    }
    CALL {
      MATCH (d:Department)
      RETURN count(d) AS departments
    }
    CALL {
      MATCH (t:Teacher)
      RETURN count(t) AS teachers
    }
    CALL {
      MATCH (p:Publication)
      RETURN count(p) AS publications
    }
    CALL {
      MATCH ()-[r:AUTHORED]->()
      RETURN count(r) AS authored
    }
    CALL {
      MATCH ()-[r:CO_AUTHOR_WITH]->()
      RETURN count(r) AS coauthor
    }
    CALL {
      MATCH ()-[r:HAS_TOPIC]->()
      RETURN count(r) AS topics
    }
    RETURN faculties, departments, teachers, publications, authored, coauthor, topics
    """
    rows = run_query(q)
    return rows[0] if rows else {
        "faculties": 0,
        "departments": 0,
        "teachers": 0,
        "publications": 0,
        "authored": 0,
        "coauthor": 0,
        "topics": 0
    }


def get_faculties():
    q = """
    MATCH (f:Faculty)
    RETURN f.faculty_id AS faculty_id,
           f.name AS name,
           f.slug AS slug,
           f.source_url AS source_url,
           f.source_name AS source_name
    ORDER BY f.faculty_id
    """
    return run_query(q)


def get_departments():
    q = """
    MATCH (d:Department)
    RETURN d.department_id AS department_id,
           d.name AS name,
           d.faculty_id AS faculty_id,
           d.slug AS slug,
           d.source_url AS source_url,
           d.source_name AS source_name
    ORDER BY d.department_id
    """
    return run_query(q)


def get_teachers():
    q = """
    MATCH (t:Teacher)
    RETURN t.teacher_id AS teacher_id,
           t.full_name AS full_name,
           t.position AS position,
           t.academic_degree AS academic_degree,
           t.academic_title AS academic_title,
           t.department_id AS department_id,
           t.faculty_id AS faculty_id,
           t.source_url AS source_url
    ORDER BY t.full_name
    """
    return run_query(q)


def get_publications():
    q = """
    MATCH (p:Publication)
    RETURN p.publication_id AS publication_id,
           p.title AS title,
           p.year AS year,
           p.doi AS doi,
           p.pub_type AS pub_type,
           p.source_type AS source_type,
           p.confidence AS confidence,
           p.source AS source,
           p.source_url AS source_url,
           p.notes AS notes
    ORDER BY p.year DESC, p.title
    """
    return run_query(q)


def get_department_options():
    q = """
    MATCH (d:Department)
    RETURN d.department_id AS department_id,
           d.name AS name,
           d.faculty_id AS faculty_id
    ORDER BY d.name
    """
    return run_query(q)


def get_faculty_options():
    q = """
    MATCH (f:Faculty)
    RETURN f.faculty_id AS faculty_id,
           f.name AS name
    ORDER BY f.name
    """
    return run_query(q)


def get_top_teachers_by_publications(limit=10):
    q = """
    MATCH (t:Teacher)-[:AUTHORED]->(p:Publication)
    RETURN t.full_name AS teacher, count(DISTINCT p) AS publications
    ORDER BY publications DESC, teacher
    LIMIT $limit
    """
    return run_query(q, {"limit": limit})


def get_top_coauthors(limit=10):
    q = """
    MATCH (a:Teacher)-[r:CO_AUTHOR_WITH]->(b:Teacher)
    RETURN a.full_name AS teacher_a,
           b.full_name AS teacher_b,
           r.weight AS shared_publications
    ORDER BY shared_publications DESC, teacher_a, teacher_b
    LIMIT $limit
    """
    return run_query(q, {"limit": limit})


def get_department_stats():
    q = """
    MATCH (d:Department)
    OPTIONAL MATCH (d)-[:HAS_TEACHER]->(t:Teacher)
    OPTIONAL MATCH (t)-[:AUTHORED]->(p:Publication)
    RETURN d.department_id AS department_id,
           d.name AS department_name,
           count(DISTINCT t) AS teachers,
           count(DISTINCT p) AS publications
    ORDER BY d.department_id
    """
    return run_query(q)


def rebuild_publication_year():
    q = """
    MATCH (p:Publication)
    WHERE p.year IS NOT NULL
    MERGE (py:PublicationYear {year: toInteger(p.year)})
    MERGE (p)-[:PUBLISHED_IN_YEAR]->(py)
    """
    execute_write(q)


def rebuild_coauthor_with():
    q_delete = """
    MATCH (:Teacher)-[r:CO_AUTHOR_WITH]->(:Teacher)
    DELETE r
    """
    q_create = """
    MATCH (a:Teacher)-[:AUTHORED]->(p:Publication)<-[:AUTHORED]-(b:Teacher)
    WHERE id(a) < id(b)
    WITH a, b, count(DISTINCT p) AS shared_pubs, collect(DISTINCT p.publication_id) AS pub_ids
    MERGE (a)-[r:CO_AUTHOR_WITH]->(b)
    SET r.weight = shared_pubs,
        r.publication_ids = pub_ids
    """
    execute_write(q_delete)
    execute_write(q_create)


def get_next_id(prefix: str, label: str, field: str, width: int = 2):
    q = f"""
    MATCH (n:{label})
    WHERE n.{field} STARTS WITH $prefix
    RETURN n.{field} AS current_id
    """
    rows = run_query(q, {"prefix": prefix})
    max_num = 0
    for row in rows:
        value = row.get("current_id")
        if not value:
            continue
        match = re.search(r"(\d+)$", value)
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"{prefix}{max_num + 1:0{width}d}"


# =========================================================
# ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ СКРЕЙПІНГУ
# =========================================================
BASE_URL = "https://www.kspu.edu/"
FACULTY_PAGE = "https://www.kspu.edu/About/Faculty.aspx"


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=25)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding
    return resp.text


def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str) -> str:
    text = text.lower().strip()
    replacements = {
        "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g",
        "д": "d", "е": "e", "є": "ie", "ж": "zh", "з": "z",
        "и": "y", "і": "i", "ї": "i", "й": "i", "к": "k",
        "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
        "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f",
        "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
        "ь": "", "ю": "iu", "я": "ia",
        "'": "", "’": "", "`": "", "ʼ": "",
    }
    out = []
    for ch in text:
        if ch in replacements:
            out.append(replacements[ch])
        elif ch.isalnum():
            out.append(ch)
        else:
            out.append("-")
    slug = "".join(out)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def extract_links(soup: BeautifulSoup):
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = clean_text(a.get_text(" ", strip=True))
        full_url = urljoin(BASE_URL, href)
        if text:
            links.append({"text": text, "url": full_url})
    return links


def scrape_faculties():
    html = fetch_html(FACULTY_PAGE)
    soup = BeautifulSoup(html, "html.parser")
    links = extract_links(soup)

    faculty_keywords = ["факультет", "педагогічний", "медичний"]
    faculties = []
    seen = set()

    for item in links:
        text = item["text"]
        url = item["url"]

        if not any(k in text.lower() for k in faculty_keywords):
            continue

        if "About/Faculty/" not in url and "Faculty.aspx" not in url:
            continue

        if len(text) < 6:
            continue

        key = (text.lower(), url.lower())
        if key in seen:
            continue
        seen.add(key)

        faculties.append({
            "name": text,
            "source_url": url
        })

    filtered = []
    for f in faculties:
        lower_name = f["name"].lower()
        if "офіс" in lower_name:
            continue
        if "декан" in lower_name:
            continue
        if "новини" in lower_name:
            continue
        filtered.append(f)

    final = []
    used_names = set()
    for f in filtered:
        name_key = f["name"].lower()
        if name_key in used_names:
            continue
        used_names.add(name_key)
        final.append(f)

    final.sort(key=lambda x: x["name"])

    for i, f in enumerate(final, start=1):
        f["faculty_id"] = f"F{i:02d}"
        f["slug"] = slugify(f["name"])

    return final


def extract_department_candidates_from_html(html: str):
    soup = BeautifulSoup(html, "html.parser")

    texts = []

    for a in soup.find_all("a"):
        txt = clean_text(a.get_text(" ", strip=True))
        if txt:
            texts.append(txt)

    for li in soup.find_all("li"):
        txt = clean_text(li.get_text(" ", strip=True))
        if txt:
            texts.append(txt)

    for tag in soup.find_all(["p", "h1", "h2", "h3", "h4", "div", "span"]):
        txt = clean_text(tag.get_text(" ", strip=True))
        if txt:
            texts.append(txt)

    department_markers = ["кафедра", "department"]
    bad_markers = [
        "декан", "новини", "розклад", "вступ", "контакти",
        "освітні програми", "наукова робота", "міжнародна діяльність",
        "практика", "студентське життя"
    ]

    result = []
    seen = set()

    for text in texts:
        lower = text.lower()

        if not any(marker in lower for marker in department_markers):
            continue

        if any(bad in lower for bad in bad_markers):
            continue

        if len(text) < 8 or len(text) > 180:
            continue

        if text.lower() in seen:
            continue
        seen.add(text.lower())
        result.append(text)

    return result


def scrape_departments_for_faculty(faculty: dict):
    urls_to_try = [
        faculty["source_url"],
        urljoin(faculty["source_url"], "Structure.aspx"),
        urljoin(faculty["source_url"], "FacultyStructure.aspx"),
    ]

    seen_urls = set()
    department_names = []

    for url in urls_to_try:
        if url in seen_urls:
            continue
        seen_urls.add(url)

        try:
            html = fetch_html(url)
            candidates = extract_department_candidates_from_html(html)
            department_names.extend(candidates)
        except Exception:
            continue

    final = []
    seen = set()
    for name in department_names:
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        final.append(name)

    final.sort()
    return final


def build_structure_dataset():
    faculties = scrape_faculties()

    departments = []
    relations = []

    dep_counter = 1

    for faculty in faculties:
        dep_names = scrape_departments_for_faculty(faculty)

        for dep_name in dep_names:
            dep_id = f"D{dep_counter:03d}"
            dep_counter += 1

            departments.append({
                "department_id": dep_id,
                "name": dep_name,
                "faculty_id": faculty["faculty_id"],
                "source_url": faculty["source_url"],
                "slug": slugify(dep_name),
            })

            relations.append({
                "faculty_id": faculty["faculty_id"],
                "department_id": dep_id
            })

    return {
        "faculties": faculties,
        "departments": departments,
        "faculty_department_relations": relations
    }


def import_structure_dataset(dataset: dict):
    faculties_rows = dataset["faculties"]
    departments_rows = dataset["departments"]
    relations_rows = dataset["faculty_department_relations"]

    faculty_query = """
    UNWIND $rows AS row
    MERGE (f:Faculty {faculty_id: row.faculty_id})
    SET f.name = row.name,
        f.slug = row.slug,
        f.source_url = row.source_url,
        f.source_name = 'kspu.edu'
    """

    department_query = """
    UNWIND $rows AS row
    MERGE (d:Department {department_id: row.department_id})
    SET d.name = row.name,
        d.slug = row.slug,
        d.faculty_id = row.faculty_id,
        d.source_url = row.source_url,
        d.source_name = 'kspu.edu'
    """

    relation_query = """
    UNWIND $rows AS row
    MATCH (f:Faculty {faculty_id: row.faculty_id})
    MATCH (d:Department {department_id: row.department_id})
    MERGE (f)-[:HAS_DEPARTMENT]->(d)
    """

    execute_many(faculty_query, faculties_rows)
    execute_many(department_query, departments_rows)
    execute_many(relation_query, relations_rows)


# =========================================================
# ШАПКА: ПІДКЛЮЧЕННЯ
# =========================================================
st.subheader("1. Підключення")

col_a, col_b = st.columns(2)

with col_a:
    if st.button("Перевірити підключення"):
        try:
            result = run_query("MATCH (n) RETURN count(n) AS cnt")
            cnt = result[0]["cnt"] if result else 0
            st.success(f"Підключення успішне. Кількість вузлів: {cnt}")
        except Exception as e:
            st.error(f"Помилка підключення: {e}")

with col_b:
    if st.button("Створити обмеження унікальності"):
        try:
            create_constraints()
            st.success("Обмеження унікальності створено.")
        except Exception as e:
            st.error(f"Не вдалося створити обмеження: {e}")


# =========================================================
# СТАН БАЗИ
# =========================================================
st.subheader("2. Стан бази")

try:
    counts = get_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Факультети", counts["faculties"])
    c2.metric("Кафедри", counts["departments"])
    c3.metric("Викладачі", counts["teachers"])
    c4.metric("Публікації", counts["publications"])

    c5, c6, c7 = st.columns(3)
    c5.metric("AUTHORED", counts["authored"])
    c6.metric("CO_AUTHOR_WITH", counts["coauthor"])
    c7.metric("HAS_TOPIC", counts["topics"])
except Exception as e:
    st.warning(f"Не вдалося отримати статистику: {e}")


# =========================================================
# ВВЕДЕННЯ ДАНИХ
# =========================================================
st.subheader("3. Довідники та введення даних")

tab1, tab2, tab3, tab4 = st.tabs([
    "Факультети",
    "Кафедри",
    "Викладачі",
    "Публікації"
])

# ----------------- ФАКУЛЬТЕТИ -----------------
with tab1:
    st.markdown("### Додати факультет")

    next_faculty_id = get_next_id("F", "Faculty", "faculty_id", width=2)

    with st.form("faculty_form", clear_on_submit=True):
        faculty_id = st.text_input("Код факультету", value=next_faculty_id)
        faculty_name = st.text_input("Назва факультету")
        faculty_source_url = st.text_input("Посилання на джерело (необов'язково)")
        submit_faculty = st.form_submit_button("Додати факультет")

        if submit_faculty:
            if not faculty_id.strip() or not faculty_name.strip():
                st.warning("Заповни код і назву факультету.")
            else:
                q = """
                MERGE (f:Faculty {faculty_id: $faculty_id})
                SET f.name = $name,
                    f.slug = $slug,
                    f.source_url = $source_url,
                    f.source_name = CASE WHEN $source_url = '' THEN null ELSE 'manual' END
                """
                execute_write(q, {
                    "faculty_id": faculty_id.strip(),
                    "name": faculty_name.strip(),
                    "slug": slugify(faculty_name.strip()),
                    "source_url": faculty_source_url.strip()
                })
                st.success("Факультет додано.")

    st.markdown("### Список факультетів")
    faculty_data = get_faculties()
    if faculty_data:
        st.dataframe(pd.DataFrame(faculty_data), use_container_width=True)
    else:
        st.info("Факультетів поки немає.")

# ----------------- КАФЕДРИ -----------------
with tab2:
    st.markdown("### Додати кафедру")

    faculty_options = get_faculty_options()
    faculty_map = {
        f"{row['faculty_id']} — {row['name']}": row["faculty_id"]
        for row in faculty_options
    }

    next_department_id = get_next_id("D", "Department", "department_id", width=3)

    with st.form("department_form", clear_on_submit=True):
        department_id = st.text_input("Код кафедри", value=next_department_id)
        department_name = st.text_input("Назва кафедри")
        faculty_choice = st.selectbox(
            "Факультет",
            options=list(faculty_map.keys()) if faculty_map else [],
            index=None,
            placeholder="Оберіть факультет"
        )
        department_source_url = st.text_input("Посилання на джерело (необов'язково)")
        submit_department = st.form_submit_button("Додати кафедру")

        if submit_department:
            if not faculty_choice:
                st.warning("Спочатку обери факультет.")
            elif not department_id.strip() or not department_name.strip():
                st.warning("Заповни код і назву кафедри.")
            else:
                faculty_id = faculty_map[faculty_choice]

                q1 = """
                MERGE (d:Department {department_id: $department_id})
                SET d.name = $name,
                    d.slug = $slug,
                    d.faculty_id = $faculty_id,
                    d.source_url = $source_url,
                    d.source_name = CASE WHEN $source_url = '' THEN null ELSE 'manual' END
                """
                q2 = """
                MATCH (f:Faculty {faculty_id: $faculty_id})
                MATCH (d:Department {department_id: $department_id})
                MERGE (f)-[:HAS_DEPARTMENT]->(d)
                """
                execute_write(q1, {
                    "department_id": department_id.strip(),
                    "name": department_name.strip(),
                    "slug": slugify(department_name.strip()),
                    "faculty_id": faculty_id,
                    "source_url": department_source_url.strip()
                })
                execute_write(q2, {
                    "faculty_id": faculty_id,
                    "department_id": department_id.strip()
                })
                st.success("Кафедру додано.")

    st.markdown("### Список кафедр")
    department_data = get_departments()
    if department_data:
        st.dataframe(pd.DataFrame(department_data), use_container_width=True)
    else:
        st.info("Кафедр поки немає.")

# ----------------- ВИКЛАДАЧІ -----------------
with tab3:
    st.markdown("### Додати викладача")

    department_options = get_department_options()
    department_map = {
        f"{row['department_id']} — {row['name']}": row
        for row in department_options
    }

    next_teacher_id = get_next_id("T", "Teacher", "teacher_id", width=4)

    with st.form("teacher_form", clear_on_submit=True):
        teacher_id = st.text_input("Код викладача", value=next_teacher_id)
        full_name = st.text_input("ПІБ")
        position = st.text_input("Посада")
        academic_degree = st.text_input("Науковий ступінь")
        academic_title = st.text_input("Вчене звання")
        department_choice = st.selectbox(
            "Кафедра",
            options=list(department_map.keys()) if department_map else [],
            index=None,
            placeholder="Оберіть кафедру"
        )
        teacher_source_url = st.text_input("Посилання на профіль (необов'язково)")
        submit_teacher = st.form_submit_button("Додати викладача")

        if submit_teacher:
            if not department_choice:
                st.warning("Спочатку обери кафедру.")
            elif not teacher_id.strip() or not full_name.strip():
                st.warning("Заповни код і ПІБ.")
            else:
                dep = department_map[department_choice]
                department_id = dep["department_id"]
                faculty_id = dep["faculty_id"]

                q1 = """
                MERGE (t:Teacher {teacher_id: $teacher_id})
                SET t.full_name = $full_name,
                    t.position = $position,
                    t.academic_degree = $academic_degree,
                    t.academic_title = $academic_title,
                    t.department_id = $department_id,
                    t.faculty_id = $faculty_id,
                    t.source_url = $source_url
                """
                q2 = """
                MATCH (d:Department {department_id: $department_id})
                MATCH (t:Teacher {teacher_id: $teacher_id})
                MERGE (d)-[:HAS_TEACHER]->(t)
                """
                execute_write(q1, {
                    "teacher_id": teacher_id.strip(),
                    "full_name": full_name.strip(),
                    "position": position.strip(),
                    "academic_degree": academic_degree.strip(),
                    "academic_title": academic_title.strip(),
                    "department_id": department_id,
                    "faculty_id": faculty_id,
                    "source_url": teacher_source_url.strip()
                })
                execute_write(q2, {
                    "department_id": department_id,
                    "teacher_id": teacher_id.strip()
                })
                st.success("Викладача додано.")

    st.markdown("### Список викладачів")
    teacher_data = get_teachers()
    if teacher_data:
        st.dataframe(pd.DataFrame(teacher_data), use_container_width=True)
    else:
        st.info("Викладачів поки немає.")

# ----------------- ПУБЛІКАЦІЇ -----------------
with tab4:
    st.markdown("### Додати публікацію")

    teacher_options = get_teachers()
    teacher_map = {
        f"{row['teacher_id']} — {row['full_name']}": row["teacher_id"]
        for row in teacher_options
    }

    next_publication_id = get_next_id("P", "Publication", "publication_id", width=5)

    with st.form("publication_form", clear_on_submit=True):
        publication_id = st.text_input("Код публікації", value=next_publication_id)
        title = st.text_area("Назва публікації")
        year_input = st.text_input("Рік")
        doi = st.text_input("DOI")
        pub_type = st.text_input("Тип публікації")
        source_type = st.text_input("Тип джерела")
        confidence = st.text_input("Рівень достовірності")
        source = st.text_input("Джерело")
        source_url = st.text_input("Посилання на джерело")
        notes = st.text_area("Примітки")
        selected_teachers = st.multiselect(
            "Автори",
            options=list(teacher_map.keys())
        )
        topics_input = st.text_input("Теми через кому (необов'язково)")
        submit_publication = st.form_submit_button("Додати публікацію")

        if submit_publication:
            if not publication_id.strip() or not title.strip():
                st.warning("Заповни код і назву публікації.")
            elif not selected_teachers:
                st.warning("Оберіть хоча б одного автора.")
            else:
                year_value = None
                if year_input.strip():
                    try:
                        year_value = int(year_input.strip())
                    except ValueError:
                        st.warning("Рік має бути числом.")
                        st.stop()

                q_pub = """
                MERGE (p:Publication {publication_id: $publication_id})
                SET p.title = $title,
                    p.year = $year,
                    p.doi = CASE WHEN $doi = '' THEN null ELSE $doi END,
                    p.pub_type = $pub_type,
                    p.source_type = $source_type,
                    p.confidence = $confidence,
                    p.source = $source,
                    p.source_url = $source_url,
                    p.notes = $notes
                """
                execute_write(q_pub, {
                    "publication_id": publication_id.strip(),
                    "title": title.strip(),
                    "year": year_value,
                    "doi": doi.strip(),
                    "pub_type": pub_type.strip(),
                    "source_type": source_type.strip(),
                    "confidence": confidence.strip(),
                    "source": source.strip(),
                    "source_url": source_url.strip(),
                    "notes": notes.strip()
                })

                authored_rows = []
                for idx, teacher_label in enumerate(selected_teachers, start=1):
                    authored_rows.append({
                        "teacher_id": teacher_map[teacher_label],
                        "publication_id": publication_id.strip(),
                        "author_order": idx
                    })

                q_authored = """
                UNWIND $rows AS row
                MATCH (t:Teacher {teacher_id: row.teacher_id})
                MATCH (p:Publication {publication_id: row.publication_id})
                MERGE (t)-[r:AUTHORED]->(p)
                SET r.author_order = row.author_order
                """
                execute_many(q_authored, authored_rows)

                topics = [t.strip() for t in topics_input.split(",") if t.strip()]
                if topics:
                    topic_rows = [{"publication_id": publication_id.strip(), "topic_name": topic} for topic in topics]
                    q_topics = """
                    UNWIND $rows AS row
                    MATCH (p:Publication {publication_id: row.publication_id})
                    MERGE (tp:Topic {name: row.topic_name})
                    MERGE (p)-[:HAS_TOPIC]->(tp)
                    """
                    execute_many(q_topics, topic_rows)

                rebuild_coauthor_with()
                rebuild_publication_year()
                st.success("Публікацію додано, зв'язки оновлено.")

    st.markdown("### Список публікацій")
    publication_data = get_publications()
    if publication_data:
        st.dataframe(pd.DataFrame(publication_data), use_container_width=True)
    else:
        st.info("Публікацій поки немає.")


# =========================================================
# АВТОЗАВАНТАЖЕННЯ СТРУКТУРИ
# =========================================================
st.subheader("4. Автозавантаження структури")

col_auto_1, col_auto_2 = st.columns(2)

with col_auto_1:
    if st.button("Отримати факультети та кафедри з сайту"):
        try:
            dataset = build_structure_dataset()
            st.session_state["kspu_dataset"] = dataset
            st.success("Структуру успішно отримано з сайту.")
        except Exception as e:
            st.error(f"Помилка під час завантаження структури: {e}")

with col_auto_2:
    if st.button("Імпортувати структуру в Neo4j"):
        dataset = st.session_state.get("kspu_dataset")
        if not dataset:
            st.warning("Спочатку отримай структуру з сайту.")
        else:
            try:
                import_structure_dataset(dataset)
                st.success(
                    f"Імпорт завершено: факультетів {len(dataset['faculties'])}, "
                    f"кафедр {len(dataset['departments'])}, "
                    f"зв'язків {len(dataset['faculty_department_relations'])}"
                )
            except Exception as e:
                st.error(f"Помилка імпорту в Neo4j: {e}")

dataset = st.session_state.get("kspu_dataset")

if dataset:
    st.markdown("### Попередній перегляд")

    auto_tab1, auto_tab2, auto_tab3 = st.tabs([
        "Факультети",
        "Кафедри",
        "Зв'язки факультет-кафедра"
    ])

    with auto_tab1:
        df_fac = pd.DataFrame(dataset["faculties"])
        st.dataframe(df_fac, use_container_width=True)

    with auto_tab2:
        df_dep = pd.DataFrame(dataset["departments"])
        st.dataframe(df_dep, use_container_width=True)

    with auto_tab3:
        df_rel = pd.DataFrame(dataset["faculty_department_relations"])
        st.dataframe(df_rel, use_container_width=True)


# =========================================================
# СЛУЖБОВІ ДІЇ
# =========================================================
st.subheader("5. Службові дії")

col_s1, col_s2 = st.columns(2)

with col_s1:
    if st.button("Побудувати PublicationYear"):
        try:
            rebuild_publication_year()
            st.success("PublicationYear побудовано.")
        except Exception as e:
            st.error(f"Помилка: {e}")

with col_s2:
    if st.button("Перерахувати CO_AUTHOR_WITH"):
        try:
            rebuild_coauthor_with()
            st.success("CO_AUTHOR_WITH перераховано.")
        except Exception as e:
            st.error(f"Помилка: {e}")


# =========================================================
# АНАЛІТИКА
# =========================================================
st.subheader("6. Аналітика")

a1, a2, a3 = st.tabs([
    "Найпродуктивніші викладачі",
    "Найсильніші зв'язки співавторства",
    "Статистика по кафедрах"
])

with a1:
    col_limit1, col_btn1 = st.columns([1, 1])
    with col_limit1:
        limit_teachers = st.number_input("Кількість записів", min_value=1, max_value=100, value=10, step=1)
    with col_btn1:
        if st.button("Показати продуктивних викладачів"):
            data = get_top_teachers_by_publications(limit=int(limit_teachers))
            if data:
                st.dataframe(pd.DataFrame(data), use_container_width=True)
            else:
                st.info("Недостатньо даних.")

with a2:
    col_limit2, col_btn2 = st.columns([1, 1])
    with col_limit2:
        limit_coauthors = st.number_input("Кількість зв'язків", min_value=1, max_value=100, value=10, step=1)
    with col_btn2:
        if st.button("Показати зв'язки співавторства"):
            data = get_top_coauthors(limit=int(limit_coauthors))
            if data:
                st.dataframe(pd.DataFrame(data), use_container_width=True)
            else:
                st.info("Недостатньо даних.")

with a3:
    if st.button("Показати статистику по кафедрах"):
        data = get_department_stats()
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("Недостатньо даних.")


# =========================================================
# ПІДВАЛ
# =========================================================
st.caption("Версія для дипломної роботи: ручне введення + автозавантаження структури + аналітика Neo4j.")
