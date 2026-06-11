from src.database import get_connection
from src.models.page import Page


class PageRepo:
    @staticmethod
    def get_all() -> list[Page]:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM pages ORDER BY sort_order").fetchall()
        conn.close()
        return [Page(**dict(r)) for r in rows]

    @staticmethod
    def get_by_id(page_id: int) -> Page | None:
        conn = get_connection()
        row = conn.execute("SELECT * FROM pages WHERE id=?", (page_id,)).fetchone()
        conn.close()
        return Page(**dict(row)) if row else None

    @staticmethod
    def get_children(parent_id: int | None) -> list[Page]:
        conn = get_connection()
        if parent_id is None:
            rows = conn.execute(
                "SELECT * FROM pages WHERE parent_id IS NULL ORDER BY sort_order"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM pages WHERE parent_id=? ORDER BY sort_order",
                (parent_id,),
            ).fetchall()
        conn.close()
        return [Page(**dict(r)) for r in rows]

    @staticmethod
    def create(page: Page) -> int:
        conn = get_connection()
        max_order = conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1"
            " FROM pages WHERE parent_id IS ?",
            (page.parent_id,),
        ).fetchone()[0]
        cursor = conn.execute(
            "INSERT INTO pages"
            " (title, parent_id, sort_order, page_type)"
            " VALUES (?, ?, ?, ?)",
            (
                page.title,
                page.parent_id,
                page.sort_order if page.sort_order else max_order,
                page.page_type,
            ),
        )
        conn.commit()
        page_id = cursor.lastrowid
        conn.close()
        return page_id

    @staticmethod
    def update(page: Page):
        conn = get_connection()
        conn.execute(
            "UPDATE pages SET title=?, parent_id=?,"
            " sort_order=?, page_type=?,"
            " updated_at=datetime('now') WHERE id=?",
            (page.title, page.parent_id, page.sort_order, page.page_type, page.id),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def delete(page_id: int):
        conn = get_connection()
        conn.execute("DELETE FROM pages WHERE id=?", (page_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def reorder(page_id: int, new_sort_order: int, new_parent_id: int | None):
        conn = get_connection()
        conn.execute(
            "UPDATE pages SET sort_order=?, parent_id=?,"
            " updated_at=datetime('now') WHERE id=?",
            (new_sort_order, new_parent_id, page_id),
        )
        conn.commit()
        conn.close()
