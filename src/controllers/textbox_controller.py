import json

from PyQt6.QtCore import QObject, pyqtSignal

from src.models.page_object import PageObject
from src.repositories.page_object_repo import PageObjectRepo


class TextboxController(QObject):
    """Handles textbox business logic."""

    meta_saved = pyqtSignal()
    meta_loaded = pyqtSignal(dict)

    def __init__(self, page_object_repo=None):
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
        blocks: list,
    ) -> None:
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
        meta = self._repo.get_textbox_meta(page_id, textbox_id)
        if meta:
            try:
                data = json.loads(meta.content)
                self.meta_loaded.emit(data)
                return data
            except (json.JSONDecodeError, ValueError):
                return None
        return None
