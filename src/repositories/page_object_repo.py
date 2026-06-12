from src.database import get_connection
from src.models.page_object import PageObject


class PageObjectRepo:
    @staticmethod
    def get_by_page(page_id: int) -> list[PageObject]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM page_objects WHERE page_id=? ORDER BY sort_order",
            (page_id,),
        ).fetchall()
        return [PageObject(**dict(r)) for r in rows]

    @staticmethod
    def get_by_id(obj_id: int) -> PageObject | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM page_objects WHERE id=?", (obj_id,)
        ).fetchone()
        return PageObject(**dict(row)) if row else None

    @staticmethod
    def create(obj: PageObject) -> int:
        conn = get_connection()
        max_order = conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1"
            " FROM page_objects WHERE page_id=?",
            (obj.page_id,),
        ).fetchone()[0]
        cursor = conn.execute(
            "INSERT INTO page_objects"
            " (page_id, object_type, content, is_checked, sort_order)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                obj.page_id,
                obj.object_type,
                obj.content,
                int(obj.is_checked),
                obj.sort_order if obj.sort_order else max_order,
            ),
        )
        conn.commit()
        return cursor.lastrowid

    @staticmethod
    def update(obj: PageObject):
        conn = get_connection()
        conn.execute(
            "UPDATE page_objects SET content=?, is_checked=?,"
            " sort_order=? WHERE id=?",
            (obj.content, int(obj.is_checked), obj.sort_order, obj.id),
        )
        conn.commit()

    @staticmethod
    def delete(obj_id: int):
        conn = get_connection()
        conn.execute("DELETE FROM page_objects WHERE id=?", (obj_id,))
        conn.commit()

    @staticmethod
    def delete_by_page(page_id: int):
        conn = get_connection()
        conn.execute("DELETE FROM page_objects WHERE page_id=?", (page_id,))
        conn.commit()
