import re
from typing import Any

from neo4j import GraphDatabase


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
    return re.sub(r"-+", "-", slug).strip("-")


class Neo4jService:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def run_query(self, query: str, params: dict[str, Any] | None = None) -> list[dict]:
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [dict(r) for r in result]

    def execute_write(self, query: str, params: dict[str, Any] | None = None) -> None:
        with self.driver.session() as session:
            session.run(query, params or {})

    def execute_many(self, query: str, rows: list[dict]) -> None:
        with self.driver.session() as session:
            session.run(query, {"rows": rows})

    # -----------------------------------------------------
    # SETUP
    # -----------------------------------------------------
    def create_constraints(self) -> None:
        queries = [
            "CREATE CONSTRAINT faculty_id_unique IF NOT EXISTS FOR (f:Faculty) REQUIRE f.faculty_id IS UNIQUE",
            "CREATE CONSTRAINT department_id_unique IF NOT EXISTS FOR (d:Department) REQUIRE d.department_id IS UNIQUE",
            "CREATE CONSTRAINT teacher_id_unique IF NOT EXISTS FOR (t:Teacher) REQUIRE t.teacher_id IS UNIQUE",
            "CREATE CONSTRAINT publication_id_unique IF NOT EXISTS FOR (p:Publication) REQUIRE p.publication_id IS UNIQUE",
            "CREATE CONSTRAINT topic_name_unique IF NOT EXISTS FOR (tp:Topic) REQUIRE tp.name IS UNIQUE",
        ]
        with self.driver.session() as session:
            for q in queries:
                session.run(q)

    def count_all_nodes(self) -> int:
        rows = self.run_query("MATCH (n) RETURN count(n) AS cnt")
        return rows[0]["cnt"] if rows else 0

    def get_counts(self) -> dict:
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
        rows = self.run_query(q)
        return rows[0] if rows else {
            "faculties": 0,
            "departments": 0,
            "teachers": 0,
            "publications": 0,
            "authored": 0,
            "coauthor": 0,
            "topics": 0,
        }

    def get_next_id(self, prefix: str, label: str, field: str, width: int) -> str:
        q = f"""
        MATCH (n:{label})
        WHERE n.{field} STARTS WITH $prefix
        RETURN n.{field} AS current_id
        """
        rows = self.run_query(q, {"prefix": prefix})
        max_num = 0
        for row in rows:
            value = row.get("current_id")
            if value:
                m = re.search(r"(\\d+)$", value)
                if m:
                    max_num = max(max_num, int(m.group(1)))
        return f"{prefix}{max_num + 1:0{width}d}"

    # -----------------------------------------------------
    # SEED
    # -----------------------------------------------------
    def seed_structure(self, faculties: list[dict], departments: list[dict]) -> None:
        faculty_rows = [
            {
                "faculty_id": row["faculty_id"],
                "name": row["name"],
                "slug": slugify(row["name"]),
            }
            for row in faculties
        ]
        department_rows = [
            {
                "department_id": row["department_id"],
                "faculty_id": row["faculty_id"],
                "name": row["name"],
                "slug": slugify(row["name"]),
            }
            for row in departments
        ]
        relation_rows = [
            {
                "faculty_id": row["faculty_id"],
                "department_id": row["department_id"],
            }
            for row in departments
        ]

        q1 = """
        UNWIND $rows AS row
        MERGE (f:Faculty {faculty_id: row.faculty_id})
        SET f.name = row.name,
            f.slug = row.slug
        """
        q2 = """
        UNWIND $rows AS row
        MERGE (d:Department {department_id: row.department_id})
        SET d.name = row.name,
            d.faculty_id = row.faculty_id,
            d.slug = row.slug
        """
        q3 = """
        UNWIND $rows AS row
        MATCH (f:Faculty {faculty_id: row.faculty_id})
        MATCH (d:Department {department_id: row.department_id})
        MERGE (f)-[:HAS_DEPARTMENT]->(d)
        """
        self.execute_many(q1, faculty_rows)
        self.execute_many(q2, department_rows)
        self.execute_many(q3, relation_rows)

    # -----------------------------------------------------
    # READ LISTS
    # -----------------------------------------------------
    def get_faculties(self) -> list[dict]:
        q = """
        MATCH (f:Faculty)
        RETURN f.faculty_id AS faculty_id,
               f.name AS name,
               f.slug AS slug
        ORDER BY f.faculty_id
        """
        return self.run_query(q)

    def get_departments(self) -> list[dict]:
        q = """
        MATCH (d:Department)
        OPTIONAL MATCH (f:Faculty)-[:HAS_DEPARTMENT]->(d)
        RETURN d.department_id AS department_id,
               d.name AS name,
               d.faculty_id AS faculty_id,
               f.name AS faculty_name,
               d.slug AS slug
        ORDER BY d.department_id
        """
        return self.run_query(q)

    def get_teachers(self) -> list[dict]:
        q = """
        MATCH (t:Teacher)
        OPTIONAL MATCH (d:Department)-[:HAS_TEACHER]->(t)
        RETURN t.teacher_id AS teacher_id,
               t.full_name AS full_name,
               t.position AS position,
               t.academic_degree AS academic_degree,
               t.academic_title AS academic_title,
               t.department_id AS department_id,
               d.name AS department_name,
               t.faculty_id AS faculty_id,
               t.orcid AS orcid,
               t.google_scholar AS google_scholar,
               t.scopus AS scopus
        ORDER BY t.full_name
        """
        return self.run_query(q)

    def get_publications(self) -> list[dict]:
        q = """
        MATCH (p:Publication)
        RETURN p.publication_id AS publication_id,
               p.title AS title,
               p.year AS year,
               p.doi AS doi,
               p.pub_type AS pub_type,
               p.source AS source
        ORDER BY p.year DESC, p.title
        """
        return self.run_query(q)

    def get_faculty_options(self) -> list[dict]:
        q = """
        MATCH (f:Faculty)
        RETURN f.faculty_id AS faculty_id, f.name AS name
        ORDER BY f.name
        """
        return self.run_query(q)

    def get_department_options(self) -> list[dict]:
        q = """
        MATCH (d:Department)
        RETURN d.department_id AS department_id,
               d.name AS name,
               d.faculty_id AS faculty_id
        ORDER BY d.name
        """
        return self.run_query(q)

    def get_teacher_options(self) -> list[dict]:
        q = """
        MATCH (t:Teacher)
        RETURN t.teacher_id AS teacher_id,
               t.full_name AS full_name
        ORDER BY t.full_name
        """
        return self.run_query(q)

    # -----------------------------------------------------
    # UPSERTS
    # -----------------------------------------------------
    def upsert_faculty(self, faculty_id: str, name: str) -> None:
        q = """
        MERGE (f:Faculty {faculty_id: $faculty_id})
        SET f.name = $name,
            f.slug = $slug
        """
        self.execute_write(q, {
            "faculty_id": faculty_id,
            "name": name,
            "slug": slugify(name),
        })

    def upsert_department(self, department_id: str, faculty_id: str, name: str) -> None:
        q1 = """
        MERGE (d:Department {department_id: $department_id})
        SET d.name = $name,
            d.slug = $slug,
            d.faculty_id = $faculty_id
        """
        q2 = """
        MATCH (f:Faculty {faculty_id: $faculty_id})
        MATCH (d:Department {department_id: $department_id})
        MERGE (f)-[:HAS_DEPARTMENT]->(d)
        """
        self.execute_write(q1, {
            "department_id": department_id,
            "faculty_id": faculty_id,
            "name": name,
            "slug": slugify(name),
        })
        self.execute_write(q2, {
            "faculty_id": faculty_id,
            "department_id": department_id,
        })

    def upsert_teacher(
        self,
        teacher_id: str,
        full_name: str,
        position: str,
        academic_degree: str,
        academic_title: str,
        department_id: str,
        faculty_id: str,
        orcid: str,
        google_scholar: str,
        scopus: str,
        source_url: str,
    ) -> None:
        q1 = """
        MERGE (t:Teacher {teacher_id: $teacher_id})
        SET t.full_name = $full_name,
            t.position = $position,
            t.academic_degree = CASE WHEN $academic_degree = '' THEN null ELSE $academic_degree END,
            t.academic_title = CASE WHEN $academic_title = '' THEN null ELSE $academic_title END,
            t.department_id = $department_id,
            t.faculty_id = $faculty_id,
            t.orcid = CASE WHEN $orcid = '' THEN null ELSE $orcid END,
            t.google_scholar = CASE WHEN $google_scholar = '' THEN null ELSE $google_scholar END,
            t.scopus = CASE WHEN $scopus = '' THEN null ELSE $scopus END,
            t.source_url = CASE WHEN $source_url = '' THEN null ELSE $source_url END
        """
        q2 = """
        MATCH (d:Department {department_id: $department_id})
        MATCH (t:Teacher {teacher_id: $teacher_id})
        MERGE (d)-[:HAS_TEACHER]->(t)
        """
        self.execute_write(q1, {
            "teacher_id": teacher_id,
            "full_name": full_name,
            "position": position,
            "academic_degree": academic_degree,
            "academic_title": academic_title,
            "department_id": department_id,
            "faculty_id": faculty_id,
            "orcid": orcid,
            "google_scholar": google_scholar,
            "scopus": scopus,
            "source_url": source_url,
        })
        self.execute_write(q2, {
            "department_id": department_id,
            "teacher_id": teacher_id,
        })

    def upsert_publication(
        self,
        publication_id: str,
        title: str,
        year: int | None,
        doi: str,
        pub_type: str,
        source: str,
        source_url: str,
        notes: str,
        teacher_ids: list[str],
        topics: list[str],
    ) -> None:
        q_pub = """
        MERGE (p:Publication {publication_id: $publication_id})
        SET p.title = $title,
            p.year = $year,
            p.doi = CASE WHEN $doi = '' THEN null ELSE $doi END,
            p.pub_type = CASE WHEN $pub_type = '' THEN null ELSE $pub_type END,
            p.source = CASE WHEN $source = '' THEN null ELSE $source END,
            p.source_url = CASE WHEN $source_url = '' THEN null ELSE $source_url END,
            p.notes = CASE WHEN $notes = '' THEN null ELSE $notes END
        """
        self.execute_write(q_pub, {
            "publication_id": publication_id,
            "title": title,
            "year": year,
            "doi": doi,
            "pub_type": pub_type,
            "source": source,
            "source_url": source_url,
            "notes": notes,
        })

        author_rows = [
            {
                "teacher_id": teacher_id,
                "publication_id": publication_id,
                "author_order": idx,
            }
            for idx, teacher_id in enumerate(teacher_ids, start=1)
        ]
        q_authored = """
        UNWIND $rows AS row
        MATCH (t:Teacher {teacher_id: row.teacher_id})
        MATCH (p:Publication {publication_id: row.publication_id})
        MERGE (t)-[r:AUTHORED]->(p)
        SET r.author_order = row.author_order
        """
        self.execute_many(q_authored, author_rows)

        if topics:
            topic_rows = [
                {"publication_id": publication_id, "topic_name": topic}
                for topic in topics
            ]
            q_topics = """
            UNWIND $rows AS row
            MATCH (p:Publication {publication_id: row.publication_id})
            MERGE (tp:Topic {name: row.topic_name})
            MERGE (p)-[:HAS_TOPIC]->(tp)
            """
            self.execute_many(q_topics, topic_rows)

        self.rebuild_coauthor_with()

    # -----------------------------------------------------
    # ANALYTICS
    # -----------------------------------------------------
    def rebuild_coauthor_with(self) -> None:
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
        self.execute_write(q_delete)
        self.execute_write(q_create)

    def get_top_teachers_by_publications(self, limit: int = 10) -> list[dict]:
        q = """
        MATCH (t:Teacher)
        OPTIONAL MATCH (t)-[:AUTHORED]->(p:Publication)
        RETURN t.full_name AS teacher,
               count(DISTINCT p) AS publications
        ORDER BY publications DESC, teacher
        LIMIT $limit
        """
        return self.run_query(q, {"limit": limit})

    def get_top_coauthors(self, limit: int = 10) -> list[dict]:
        q = """
        MATCH (a:Teacher)-[r:CO_AUTHOR_WITH]->(b:Teacher)
        RETURN a.full_name AS teacher_a,
               b.full_name AS teacher_b,
               r.weight AS shared_publications
        ORDER BY shared_publications DESC, teacher_a, teacher_b
        LIMIT $limit
        """
        return self.run_query(q, {"limit": limit})

    def get_department_stats(self) -> list[dict]:
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
        return self.run_query(q)

    def get_teacher_activity_index(self) -> list[dict]:
        q = """
        MATCH (t:Teacher)
        OPTIONAL MATCH (t)-[:AUTHORED]->(p:Publication)
        WITH t, count(DISTINCT p) AS pubs
        OPTIONAL MATCH (t)-[r:CO_AUTHOR_WITH]-(:Teacher)
        WITH t, pubs,
             count(DISTINCT r) AS coauthor_links,
             coalesce(sum(r.weight), 0) AS coauthor_strength
        RETURN t.full_name AS teacher,
               pubs,
               coauthor_links,
               coauthor_strength,
               round((pubs * 3.0 + coauthor_links * 2.0 + coauthor_strength * 1.0) * 100) / 100 AS activity_index
        ORDER BY activity_index DESC, teacher
        """
        return self.run_query(q)
