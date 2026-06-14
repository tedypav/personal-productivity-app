import json

from PyQt6.QtCore import QObject, pyqtSignal

from src.models.page_object import PageObject
from src.repositories.page_object_repo import PageObjectRepo


class TableController(QObject):
    """Handles table business logic."""

    meta_saved = pyqtSignal()
    meta_loaded = pyqtSignal(dict)
    cell_changed = pyqtSignal(int, int, int, str)

    def __init__(self, page_object_repo=None):
        super().__init__()
        self._repo = page_object_repo or PageObjectRepo()

    def save_meta(
        self,
        page_id: int,
        table_id: int,
        x: int,
        y: int,
        width: int,
        height: int,
        rows: int,
        cols: int,
        data: list,
        has_header: bool,
    ) -> None:
        meta = self._repo.get_table_meta(page_id, table_id)
        content = json.dumps(
            {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "rows": rows,
                "cols": cols,
                "data": data,
                "has_header": has_header,
            }
        )
        if meta:
            meta.content = content
            self._repo.update(meta)
        else:
            obj = PageObject(
                page_id=page_id,
                object_type="table_meta",
                content=content,
                sort_order=table_id * 100 + 50,
            )
            self._repo.create(obj)
        self.meta_saved.emit()

    def load_meta(self, page_id: int, table_id: int) -> dict | None:
        meta = self._repo.get_table_meta(page_id, table_id)
        if meta:
            try:
                data = json.loads(meta.content)
                self.meta_loaded.emit(data)
                return data
            except (json.JSONDecodeError, ValueError):
                return None
        return None

    def update_cell(
        self, page_id: int, table_id: int, row: int, col: int, content: str
    ) -> None:
        meta = self._repo.get_table_meta(page_id, table_id)
        if meta:
            data = json.loads(meta.content)
            data["data"][row][col] = content
            meta.content = json.dumps(data)
            self._repo.update(meta)
            self.cell_changed.emit(row, col, table_id, content)

    def delete_meta(self, table_id: int) -> None:
        self._repo.delete(table_id)
