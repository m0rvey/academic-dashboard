from datetime import date, timedelta

from src.core.config import DAILY_LOAD_LIMIT, EXAM_PRIORITY_MULTIPLIER, EXAM_TAGS
from src.core.models import get_clean_date


def get_period_dates(period: str) -> tuple:
    today = date.today()
    if period == "today":
        return today.isoformat(), today.isoformat()
    elif period == "week":
        return (today - timedelta(days=6)).isoformat(), today.isoformat()
    elif period == "month":
        return (today - timedelta(days=29)).isoformat(), today.isoformat()
    return None, None


class StatsRepository:
    """Репозиторий для агрегации KPI и анализа нагрузки."""

    def __init__(self, db_connection) -> None:
        self.db_conn = db_connection

    def get_daily_load_for_date(self, target_date: str) -> tuple:
        try:
            target_date_obj = date.fromisoformat(get_clean_date(target_date))
        except ValueError:
            target_date_obj = date.today()

        target_date_str = target_date_obj.isoformat()

        with self.db_conn.connection() as conn:
            cursor = conn.execute(
                "SELECT SUM(effort_score) as total FROM tasks WHERE deadline = ? AND status != 2",
                (target_date_str,),
            )
            row = cursor.fetchone()
            total_load = row["total"] if row["total"] is not None else 0
            return total_load, total_load > DAILY_LOAD_LIMIT

    def get_kpi_stats(self, period: str = "all") -> dict:
        today_str = date.today().isoformat()
        start_date, end_date = get_period_dates(period)

        where_clause = ""
        params = []
        if start_date and end_date:
            where_clause = " WHERE deadline BETWEEN ? AND ?"
            params = [start_date, end_date]

        exam_placeholders = ", ".join("?" for _ in EXAM_TAGS)
        priority_expr = f"""(
            CAST(effort_score AS REAL) / (
                (CASE
                    WHEN (julianday(deadline) - julianday(date('now', 'localtime'))) < 0 THEN 0
                    ELSE CAST(julianday(deadline) - julianday(date('now', 'localtime')) AS INTEGER)
                END) + 1
            ) * CASE
                WHEN EXISTS (
                    SELECT 1 FROM task_tags tt2
                    JOIN tags tg2 ON tt2.tag_id = tg2.id
                    WHERE tt2.task_id = tasks.id AND tg2.name IN ({exam_placeholders})
                ) THEN {EXAM_PRIORITY_MULTIPLIER}
                ELSE 1.0
            END
        )"""

        query = f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status != 2 AND deadline < ? THEN 1 ELSE 0 END) as overdue,
                SUM(CASE WHEN status != 2 AND {priority_expr} >= 2.5 THEN 1 ELSE 0 END) as high_priority
            FROM tasks
            {where_clause}
        """
        query_params = [today_str] + list(EXAM_TAGS) + params

        with self.db_conn.connection() as conn:
            row = conn.execute(query, query_params).fetchone()
            total = row["total"] if row["total"] is not None else 0
            completed = row["completed"] if row["completed"] is not None else 0
            overdue = row["overdue"] if row["overdue"] is not None else 0
            high_priority_count = row["high_priority"] if row["high_priority"] is not None else 0

            return {
                "total": total,
                "completed": completed,
                "overdue": overdue,
                "high_priority": high_priority_count,
            }

    def get_subject_load(self, period: str = "all") -> dict:
        start_date, end_date = get_period_dates(period)
        query = "SELECT subject, SUM(effort_score) as load FROM tasks WHERE status != 2"
        params = []
        if start_date and end_date:
            query += " AND deadline BETWEEN ? AND ?"
            params = [start_date, end_date]
        query += " GROUP BY subject"

        with self.db_conn.connection() as conn:
            cursor = conn.execute(query, params)
            return {row["subject"]: row["load"] for row in cursor.fetchall()}

    def get_tag_load(self, period: str = "all") -> dict:
        start_date, end_date = get_period_dates(period)
        query = """
            SELECT tg.name, SUM(t.effort_score) as load
            FROM tasks t
            JOIN task_tags tt ON t.id = tt.task_id
            JOIN tags tg ON tt.tag_id = tg.id
            WHERE t.status != 2
        """
        params = []
        if start_date and end_date:
            query += " AND t.deadline BETWEEN ? AND ?"
            params = [start_date, end_date]
        query += " GROUP BY tg.name"

        with self.db_conn.connection() as conn:
            cursor = conn.execute(query, params)
            return {row["name"]: row["load"] for row in cursor.fetchall()}

    def get_completed_tasks_by_day_last_7_days(self) -> dict:
        today = date.today()
        result = {}
        for i in range(7):
            d = today - timedelta(days=6 - i)
            result[d.isoformat()] = 0

        with self.db_conn.connection() as conn:
            cursor = conn.execute(
                """
                SELECT deadline, COUNT(*) as count
                FROM tasks
                WHERE status = 2 AND deadline BETWEEN ? AND ?
                GROUP BY deadline
                """,
                ((today - timedelta(days=6)).isoformat(), today.isoformat()),
            )
            for row in cursor.fetchall():
                d_str = row["deadline"]
                if d_str in result:
                    result[d_str] = row["count"]
        return result
