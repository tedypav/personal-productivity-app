"""Textbox business logic controller — meta CRUD for rich text blocks."""

from __future__ import annotations

import json
import logging

from PyQt6.QtCore import QObject, pyqtSignal

from src.models.page_object import PageObject
from src.repositories.page_object_repo import PageObjectRepo

logger = logging.getLogger(__name__)


class TextboxController(QObject):
    """Handles textbox business logic."""

    meta_saved = pyqtSignal()
    meta_loaded = pyqtSignal(dict)

    def __init__(self, page_object_repo: PageObjectRepo | None = None) -> None:
        super().__init__()
        self._repo = page_object_repo or PageObjectRepo()

    def save_meta(
        self,
        page_id: int,
        textbox_id: int,
        x: int,
        y: int,
        width: int,
        height: int,
        title: str,
        blocks: list[dict],
    ) -> None:
        """Save or update textbox position, size, title, and block content."""
        meta = self._repo.get_textbox_meta(page_id, textbox_id)
        content = json.dumps(
            {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "title": title,
                "blocks": blocks,
            }
        )
        if meta:
            meta.content = content
            self._repo.update(meta)
        else:
            obj = PageObject(
                page_id=page_id,
                object_type="textbox_meta",
                content=content,
                sort_order=textbox_id * 100 + 50,
            )
            self._repo.create(obj)
        self.meta_saved.emit()

    def load_meta(self, page_id: int, textbox_id: int) -> dict | None:
        """Load textbox metadata. Returns None if not found or corrupt."""
        meta = self._repo.get_textbox_meta(page_id, textbox_id)
        if meta:
            try:
                data = json.loads(meta.content)
                self.meta_loaded.emit(data)
                return data
            except (json.JSONDecodeError, ValueError):
                logger.warning(
                    "Corrupt textbox meta for textbox %d on page %d",
                    textbox_id,
                    page_id,
                )
                return None
        return None
