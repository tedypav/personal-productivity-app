"""Editor business logic controller — page loading, object CRUD."""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from src.models.page_object import PageObject
from src.repositories.page_object_repo import PageObjectRepo
from src.repositories.page_repo import PageRepo


class EditorController(QObject):
    """Handles editor business logic."""

    page_loaded = pyqtSignal(dict)
    object_loaded = pyqtSignal(list)
    object_deleted = pyqtSignal(int)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        page_repo: PageRepo | None = None,
        page_object_repo: PageObjectRepo | None = None,
    ) -> None:
        super().__init__()
        self._page_repo = page_repo or PageRepo()
        self._obj_repo = page_object_repo or PageObjectRepo()

    def load_page(self, page_id: int) -> dict | None:
        """Load a page and its children (if folder). Returns page data or None."""
        page = self._page_repo.get_by_id(page_id)
        if page:
            if page.page_type == "folder":
                children = self._page_repo.get_children(page_id)
            else:
                children = []
            data = {"page": page, "children": children}
            self.page_loaded.emit(data)
            return data
        return None

    def get_objects(self, page_id: int) -> list[PageObject]:
        """Return all content objects for a page."""
        objects = self._obj_repo.get_by_page(page_id)
        self.object_loaded.emit(objects)
        return objects

    def delete_object(self, obj_id: int) -> None:
        """Delete a content object by ID."""
        obj = self._obj_repo.get_by_id(obj_id)
        if obj:
            self._obj_repo.delete(obj_id)
            self.object_deleted.emit(obj_id)

    def update_object(self, obj_id: int, content: str) -> None:
        """Update the content of an existing object."""
        obj = self._obj_repo.get_by_id(obj_id)
        if obj:
            obj.content = content
            self._obj_repo.update(obj)

    def get_table_meta(self, page_id: int, table_id: int) -> PageObject | None:
        """Return the table metadata record for a given table block."""
        return self._obj_repo.get_table_meta(page_id, table_id)

    def delete_table_meta(self, table_id: int) -> None:
        """Delete a table metadata record."""
        self._obj_repo.delete(table_id)

    def create_object(
        self,
        page_id: int,
        object_type: str,
        content: str,
        sort_order: int = 0,
    ) -> int:
        """Create a new content object and return its ID."""
        obj = PageObject(
            page_id=page_id,
            object_type=object_type,
            content=content,
            sort_order=sort_order,
        )
        return self._obj_repo.create(obj)

    def get_object_meta(self, page_id: int, checklist_id: int) -> PageObject | None:
        """Return the checklist metadata record for a given checklist block."""
        return self._obj_repo.get_meta(page_id, checklist_id)
