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
            "UPDATE page_objects SET content=?, is_checked=?, sort_order=? WHERE id=?",
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

    @staticmethod
    def get_meta(page_id: int, checklist_id: int) -> PageObject | None:
        conn = get_connection()
        sort_order = checklist_id * 100 + 50
        row = conn.execute(
            "SELECT * FROM page_objects WHERE page_id=?"
            " AND object_type='checklist_meta' AND sort_order=?",
            (page_id, sort_order),
        ).fetchone()
        return PageObject(**dict(row)) if row else None

    @staticmethod
    def get_table_meta(page_id: int, table_id: int) -> PageObject | None:
        conn = get_connection()
        sort_order = table_id * 100 + 50
        row = conn.execute(
            "SELECT * FROM page_objects WHERE page_id=?"
            " AND object_type='table_meta' AND sort_order=?",
            (page_id, sort_order),
        ).fetchone()
        return PageObject(**dict(row)) if row else None

    @staticmethod
    def get_textbox_meta(page_id: int, textbox_id: int) -> PageObject | None:
        conn = get_connection()
        sort_order = textbox_id * 100 + 50
        row = conn.execute(
            "SELECT * FROM page_objects WHERE page_id=?"
            " AND object_type='textbox_meta' AND sort_order=?",
            (page_id, sort_order),
        ).fetchone()
        return PageObject(**dict(row)) if row else None

    @staticmethod
    def copy_objects(source_page_id: int, dest_page_id: int) -> int:
        """Copy all objects from source to destination page."""
        objects = PageObjectRepo.get_by_page(source_page_id)
        for obj in objects:
            new_obj = PageObject(
                page_id=dest_page_id,
                object_type=obj.object_type,
                content=obj.content,
                is_checked=obj.is_checked,
                sort_order=obj.sort_order,
            )
            PageObjectRepo.create(new_obj)
        return len(objects)
