from src.database import get_connection
from src.models.task import Task


class TaskRepo:
    @staticmethod
    def get_by_block(block_id: int) -> list[Task]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM tasks WHERE content_block_id=? ORDER BY sort_order",
            (block_id,),
        ).fetchall()
        conn.close()
        return [Task(**dict(r)) for r in rows]

    @staticmethod
    def create(task: Task) -> int:
        conn = get_connection()
        max_order = conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1"
            " FROM tasks WHERE content_block_id=?",
            (task.content_block_id,),
        ).fetchone()[0]
        cursor = conn.execute(
            "INSERT INTO tasks"
            " (content_block_id, text, is_checked,"
            " recurrence_type, due_date,"
            " parent_task_id, sort_order)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                task.content_block_id,
                task.text,
                int(task.is_checked),
                task.recurrence_type,
                task.due_date,
                task.parent_task_id,
                max_order,
            ),
        )
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        return task_id

    @staticmethod
    def update(task: Task):
        conn = get_connection()
        conn.execute(
            "UPDATE tasks SET text=?, is_checked=?,"
            " recurrence_type=?, due_date=?,"
            " sort_order=? WHERE id=?",
            (
                task.text,
                int(task.is_checked),
                task.recurrence_type,
                task.due_date,
                task.sort_order,
                task.id,
            ),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def delete(task_id: int):
        conn = get_connection()
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def delete_by_block(block_id: int):
        conn = get_connection()
        conn.execute("DELETE FROM tasks WHERE content_block_id=?", (block_id,))
        conn.commit()
        conn.close()
