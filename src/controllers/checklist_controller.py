"""Checklist business logic controller — meta and item CRUD."""

from __future__ import annotations

import json
import logging

from PyQt6.QtCore import QObject, pyqtSignal

from src.models.page_object import PageObject
from src.repositories.page_object_repo import PageObjectRepo

logger = logging.getLogger(__name__)


class ChecklistController(QObject):
    """Handles checklist business logic."""

    meta_saved = pyqtSignal()
    meta_loaded = pyqtSignal(dict)
    item_created = pyqtSignal(int)
    item_deleted = pyqtSignal(int)

    def __init__(self, page_object_repo: PageObjectRepo | None = None) -> None:
        super().__init__()
        self._repo = page_object_repo or PageObjectRepo()

    def save_meta(
        self,
        page_id: int,
        checklist_id: int,
        x: int,
        y: int,
        width: int,
        height: int,
        title: str,
    ) -> None:
        """Save or update the position, size, and title of a checklist widget."""
        meta = self._repo.get_meta(page_id, checklist_id)
        content = json.dumps(
            {"x": x, "y": y, "width": width, "height": height, "title": title}
        )
        if meta:
            meta.content = content
            self._repo.update(meta)
        else:
            obj = PageObject(
                page_id=page_id,
                object_type="checklist_meta",
                content=content,
                sort_order=checklist_id * 100 + 50,
            )
            self._repo.create(obj)
        self.meta_saved.emit()

    def load_meta(self, page_id: int, checklist_id: int) -> dict | None:
        """Load checklist metadata. Returns None if not found or corrupt."""
        meta = self._repo.get_meta(page_id, checklist_id)
        if meta:
            try:
                data = json.loads(meta.content)
                self.meta_loaded.emit(data)
                return data
            except (json.JSONDecodeError, ValueError):
                logger.warning(
                    "Corrupt checklist meta for checklist %d on page %d",
                    checklist_id,
                    page_id,
                )
                return None
        return None

    def create_item(
        self, page_id: int, checklist_id: int, text: str = ""
    ) -> int | None:
        """Create a new checklist item and return its ID."""
        obj = PageObject(
            page_id=page_id,
            object_type="checkbox",
            content=json.dumps({"text": text, "checked": False}),
            sort_order=checklist_id * 100 + 50,
        )
        obj.id = self._repo.create(obj)
        self.item_created.emit(obj.id)
        return obj.id

    def delete_item(self, obj_id: int) -> None:
        """Delete a checklist item by ID."""
        self._repo.delete(obj_id)
        self.item_deleted.emit(obj_id)

    def update_item(self, obj_id: int, checked: bool, text: str) -> None:
        """Update the checked state and text of a checklist item."""
        obj = self._repo.get_by_id(obj_id)
        if obj:
            obj.content = json.dumps({"checked": checked, "text": text})
            self._repo.update(obj)
