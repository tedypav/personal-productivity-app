"""CRUD operations for the pages table."""

from src.database import get_connection
from src.models.page import Page


class PageRepo:
    """Static-method repository for page database operations."""

    @staticmethod
    def get_all() -> list[Page]:
        """Return all pages ordered by sort_order."""
        conn = get_connection()
        rows = conn.execute("SELECT * FROM pages ORDER BY sort_order").fetchall()
        return [Page(**dict(r)) for r in rows]

    @staticmethod
    def get_by_id(page_id: int) -> Page | None:
        """Return a page by its primary key, or None if not found."""
        conn = get_connection()
        row = conn.execute("SELECT * FROM pages WHERE id=?", (page_id,)).fetchone()
        return Page(**dict(row)) if row else None

    @staticmethod
    def get_children(parent_id: int | None) -> list[Page]:
        """Return direct children of a parent page, ordered by sort_order.

        Pass parent_id=None to get root-level pages.
        """
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
        return [Page(**dict(r)) for r in rows]

    @staticmethod
    def create(page: Page) -> int:
        """Insert a new page and return its auto-generated ID.

        Auto-computes sort_order as MAX+1 among siblings if not set.
        """
        conn = get_connection()
        max_order = conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM pages WHERE parent_id IS ?",
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
        assert page_id is not None
        return page_id

    @staticmethod
    def update(page: Page) -> None:
        """Update an existing page's fields."""
        conn = get_connection()
        conn.execute(
            "UPDATE pages SET title=?, parent_id=?,"
            " sort_order=?, page_type=?,"
            " updated_at=datetime('now') WHERE id=?",
            (page.title, page.parent_id, page.sort_order, page.page_type, page.id),
        )
        conn.commit()

    @staticmethod
    def delete(page_id: int) -> None:
        """Delete a page by ID. Cascade handles children and objects."""
        conn = get_connection()
        conn.execute("DELETE FROM pages WHERE id=?", (page_id,))
        conn.commit()

    @staticmethod
    def reorder(page_id: int, new_sort_order: int, new_parent_id: int | None) -> None:
        """Update a page's sort_order and parent_id."""
        conn = get_connection()
        conn.execute(
            "UPDATE pages SET sort_order=?, parent_id=?,"
            " updated_at=datetime('now') WHERE id=?",
            (new_sort_order, new_parent_id, page_id),
        )
        conn.commit()

    @staticmethod
    def has_sibling_with_name(
        parent_id: int | None, name: str, exclude_id: int | None = None
    ) -> bool:
        """Check if a sibling with the given name already exists.

        Args:
            parent_id: Parent page ID (None for root level).
            name: Title to check for.
            exclude_id: Page ID to exclude from the check (for renames).
        """
        conn = get_connection()
        if parent_id is None:
            if exclude_id:
                row = conn.execute(
                    "SELECT 1 FROM pages WHERE parent_id IS NULL AND title=? AND id!=?",
                    (name, exclude_id),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT 1 FROM pages WHERE parent_id IS NULL AND title=?",
                    (name,),
                ).fetchone()
        else:
            if exclude_id:
                row = conn.execute(
                    "SELECT 1 FROM pages WHERE parent_id=? AND title=? AND id!=?",
                    (parent_id, name, exclude_id),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT 1 FROM pages WHERE parent_id=? AND title=?",
                    (parent_id, name),
                ).fetchone()
        return row is not None
