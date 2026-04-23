    def import_teachers(self, teachers: list[dict]) -> None:
        if not teachers:
            return

        q1 = """
        UNWIND $rows AS row
        MERGE (t:Teacher {teacher_id: row.teacher_id})
        SET t.full_name = row.full_name,
            t.position = CASE WHEN row.position = '' THEN null ELSE row.position END,
            t.academic_degree = CASE WHEN row.academic_degree = '' THEN null ELSE row.academic_degree END,
            t.academic_title = CASE WHEN row.academic_title = '' THEN null ELSE row.academic_title END,
            t.department_id = row.department_id,
            t.faculty_id = row.faculty_id,
            t.orcid = CASE WHEN row.orcid = '' THEN null ELSE row.orcid END,
            t.google_scholar = CASE WHEN row.google_scholar = '' THEN null ELSE row.google_scholar END,
            t.scopus = CASE WHEN row.scopus = '' THEN null ELSE row.scopus END,
            t.source_url = CASE WHEN row.source_url = '' THEN null ELSE row.source_url END
        """

        q2 = """
        UNWIND $rows AS row
        MATCH (d:Department {department_id: row.department_id})
        MATCH (t:Teacher {teacher_id: row.teacher_id})
        MERGE (d)-[:HAS_TEACHER]->(t)
        """

        self.execute_many(q1, teachers)
        self.execute_many(q2, teachers)
