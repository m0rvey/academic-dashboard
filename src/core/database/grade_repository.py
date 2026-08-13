class GradeRepository:
    """Репозиторий для вычисления статистики по оценкам и успеваемости."""

    def __init__(self, db_connection) -> None:
        self.db_conn = db_connection

    def get_grades_stats(self) -> dict:
        """Получает общую успеваемость."""
        with self.db_conn.connection() as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(grade) as total_count,
                    AVG(grade) as gpa,
                    SUM(CASE WHEN grade = 5 THEN 1 ELSE 0 END) as count_5,
                    SUM(CASE WHEN grade = 4 THEN 1 ELSE 0 END) as count_4,
                    SUM(CASE WHEN grade = 3 THEN 1 ELSE 0 END) as count_3,
                    SUM(CASE WHEN grade = 2 THEN 1 ELSE 0 END) as count_2
                FROM tasks
                WHERE status = 2 AND grade IS NOT NULL
                """)
            row = cursor.fetchone()
            if not row or row["total_count"] == 0:
                return {}
            return {
                "total_count": row["total_count"],
                "gpa": row["gpa"],
                "count_5": row["count_5"],
                "count_4": row["count_4"],
                "count_3": row["count_3"],
                "count_2": row["count_2"],
            }

    def get_subject_grades_gpa(self) -> dict:
        """Получает средний балл по каждому предмету."""
        with self.db_conn.connection() as conn:
            cursor = conn.execute("""
                SELECT subject, AVG(grade) as gpa, COUNT(grade) as count
                FROM tasks
                WHERE status = 2 AND grade IS NOT NULL
                GROUP BY subject
                """)
            return {row["subject"]: {"gpa": row["gpa"], "count": row["count"]} for row in cursor.fetchall()}
