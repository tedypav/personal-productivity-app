import json

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.models.page_object import PageObject
from src.repositories.page_object_repo import PageObjectRepo
from src.ui.objects.resizable_mixin import ResizableMixin

__all__ = ["ChecklistWidget"]


class ChecklistWidget(ResizableMixin, QWidget):
    """A container for a group of checkboxes with an add button."""

    object_changed = pyqtSignal(int, bool, str)
    object_delete_requested = pyqtSignal(int)
    item_delete_requested = pyqtSignal(int)

    def __init__(self, checklist_id, page_id=None, parent=None):
        super().__init__(parent)
        self.checklist_id = checklist_id
        self.page_id = page_id
        self._init_resizable_state()
        self.setObjectName("checklist")
        self.setStyleSheet(
            "#checklist {"
            " background-color: #FFFFFF;"
            " border: 1px solid #F7D1DC;"
            " border-radius: 12px;"
            "}"
            "#checklist > QWidget {"
            " background-color: transparent;"
            "}"
        )
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(36)
        header.setObjectName("checklist_header")
        header.setCursor(Qt.CursorShape.OpenHandCursor)
        header.setStyleSheet(
            "#checklist_header {"
            " background-color: #FFF0F3;"
            " border-top-left-radius: 12px;"
            " border-bottom: 1px solid #F7D1DC;"
            "}"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 4, 12, 4)
        header_layout.setSpacing(6)

        title = QLineEdit("Checklist")
        title.setPlaceholderText("Checklist")
        title.setStyleSheet(
            "QLineEdit { border: none; background: transparent;"
            " font-family: 'Inter', sans-serif; font-size: 11px;"
            " color: #8B6B7B; font-weight: 600; padding: 0; }"
        )
        title.returnPressed.connect(self._on_title_changed)
        title.editingFinished.connect(self._on_title_changed)
        self._title_edit = title
        header_layout.addWidget(title)
        header_layout.addStretch()

        delete_btn = QToolButton()
        delete_btn.setText("×")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(
            "QToolButton {"
            " border: none; font-size: 14px;"
            " color: #4B5563; background: transparent;"
            " }"
            " QToolButton:hover {"
            " color: #EF4444;"
            " }"
        )
        delete_btn.clicked.connect(self._delete_checklist)
        header_layout.addWidget(delete_btn)

        self._header = header
        self._layout.addWidget(header)

        self._checkboxes_layout = QVBoxLayout()
        self._checkboxes_layout.setContentsMargins(0, 0, 0, 0)
        self._checkboxes_layout.setSpacing(6)
        self._layout.addLayout(self._checkboxes_layout)

        add_btn = QPushButton("+ Add item")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(
            "QPushButton { border: none; font-size: 12px; color: #CFA6D6;"
            " padding: 8px 12px; text-align: left;"
            " font-family: 'Inter', sans-serif;"
            " background: #FFFFFF; }"
            " QPushButton:hover { color: #9b59b6; }"
        )
        add_btn.clicked.connect(lambda: self._add_item())
        self._layout.addWidget(add_btn)
        self.setMouseTracking(True)
        self._install_border_filter(self)

    def _install_border_filter(self, widget):
        widget.setMouseTracking(True)
        for child in widget.findChildren(QWidget):
            child.setMouseTracking(True)
            child.installEventFilter(self)

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent, QMouseEvent

        if obj is self:
            return super().eventFilter(obj, event)
        if isinstance(event, QKeyEvent):
            is_del = event.type() == QEvent.Type.KeyPress
            is_delete_key = event.key() == Qt.Key.Key_Delete
            is_ctrl_d = (
                event.key() == Qt.Key.Key_D
                and event.modifiers() & Qt.KeyboardModifier.ControlModifier
            )
            if is_del and (is_delete_key or is_ctrl_d):
                for i in range(self._checkboxes_layout.count()):
                    w = self._checkboxes_layout.itemAt(i).widget()
                    if w and hasattr(w, "obj_id") and w.isAncestorOf(obj):
                        is_task = hasattr(
                            w, "_text_edit"
                        ) and w._text_edit.isAncestorOf(obj)
                        if is_task:
                            self.item_delete_requested.emit(w.obj_id)
                        else:
                            self.object_delete_requested.emit(self.checklist_id)
                        event.accept()
                        return True
            return super().eventFilter(obj, event)
        if not isinstance(event, QMouseEvent):
            return super().eventFilter(obj, event)
        pos = obj.mapTo(self, event.position().toPoint())
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                for i in range(self._checkboxes_layout.count()):
                    w = self._checkboxes_layout.itemAt(i).widget()
                    if w and hasattr(w, "obj_id") and w.isAncestorOf(obj):
                        if hasattr(w, "_text_edit") and obj is w._text_edit:
                            pass
                        else:
                            w.focus_text()
                        break
                edge = self._detect_edge(pos)
                if edge:
                    self._resizing = True
                    self._resize_edge = edge
                    self._resize_start = event.globalPosition().toPoint()
                    self._resize_origin = (
                        self.x(),
                        self.y(),
                        self.width(),
                        self.height(),
                    )
                    event.accept()
                    return True
        if event.type() == QEvent.Type.MouseMove:
            edge = self._detect_edge(pos)
            if edge and not self._resizing and not self._dragging:
                obj.setCursor(self._edge_cursor(edge))
            elif not edge and not self._resizing and not self._dragging:
                obj.setCursor(Qt.CursorShape.ArrowCursor)
        return super().eventFilter(obj, event)

    def _refresh_size(self):
        header_h = 36
        add_btn_h = 32
        item_h = 42
        spacing = self._checkboxes_layout.spacing()
        n = self._checkboxes_layout.count()
        items_h = n * item_h + max(0, n - 1) * spacing
        h = header_h + items_h + add_btn_h
        if self._user_width:
            w = max(self._MIN_W, self._user_width)
            self.setFixedWidth(w)
        self.resize(self.width(), h)

    def _save_meta(self):
        repo = PageObjectRepo()
        meta = repo.get_meta(self.page_id, self.checklist_id)
        content = json.dumps(
            {
                "x": self.x(),
                "y": self.y(),
                "width": self.width(),
                "title": self._title_edit.text(),
            }
        )
        if meta:
            meta.content = content
            repo.update(meta)
        else:
            obj = PageObject(
                page_id=self.page_id,
                object_type="checklist_meta",
                content=content,
                sort_order=self.checklist_id * 100 + 50,
            )
            repo.create(obj)

    def _load_meta(self):
        meta = PageObjectRepo().get_meta(self.page_id, self.checklist_id)
        if meta:
            data = json.loads(meta.content)
            self._user_width = data.get("width")
            title = data.get("title", "Checklist")
            self._title_edit.setText(title)
            x = data.get("x")
            y = data.get("y")
            if x is not None and y is not None:
                self._loaded_pos = (x, y)
                self.move(x, y)
            else:
                self._loaded_pos = None
        else:
            self._loaded_pos = None

    def _add_item(self, text="", checked=False):
        from src.ui.objects.checkbox_widget import CheckboxWidget

        obj = PageObject(
            page_id=self.page_id,
            object_type="checkbox",
            content=json.dumps({"text": text, "checked": checked}),
            is_checked=checked,
        )
        obj.id = PageObjectRepo().create(obj)
        widget = CheckboxWidget(
            obj_id=obj.id,
            text=text,
            checked=checked,
        )
        widget.changed.connect(self.object_changed)
        widget.delete_requested.connect(self.item_delete_requested)
        widget.enter_pressed.connect(self._on_enter_pressed)
        self._checkboxes_layout.addWidget(widget)
        self._install_border_filter(widget)
        self._refresh_size()
        return widget

    def _on_title_changed(self):
        self._save_meta()

    def _on_enter_pressed(self, obj_id):
        for i in range(self._checkboxes_layout.count()):
            w = self._checkboxes_layout.itemAt(i).widget()
            if w and hasattr(w, "obj_id") and w.obj_id == obj_id:
                text = w._text_edit.text()
                if text.strip():
                    new_widget = self._add_item()
                    new_widget.focus_text()
                else:
                    next_i = i + 1
                    if next_i < self._checkboxes_layout.count():
                        next_w = self._checkboxes_layout.itemAt(next_i).widget()
                        if next_w and hasattr(next_w, "focus_text"):
                            next_w.focus_text()
                break

    def _delete_checklist(self):
        for i in range(self._checkboxes_layout.count()):
            widget = self._checkboxes_layout.itemAt(i).widget()
            if widget and hasattr(widget, "obj_id"):
                PageObjectRepo().delete(widget.obj_id)
        self.object_delete_requested.emit(self.checklist_id)
        self.deleteLater()

    def _min_height(self):
        return 36 + 42 + 32

    def _on_resize_complete(self):
        self._scale_rows_to_fit()

    def keyPressEvent(self, event):
        is_delete_key = event.key() == Qt.Key.Key_Delete
        is_ctrl_d = (
            event.key() == Qt.Key.Key_D
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        )
        if is_delete_key or is_ctrl_d:
            from PyQt6.QtWidgets import QApplication

            focused = QApplication.focusWidget()
            if focused:
                for i in range(self._checkboxes_layout.count()):
                    w = self._checkboxes_layout.itemAt(i).widget()
                    if w and hasattr(w, "obj_id") and w.isAncestorOf(focused):
                        is_task = hasattr(
                            w, "_text_edit"
                        ) and w._text_edit.isAncestorOf(focused)
                        if is_task:
                            self.item_delete_requested.emit(w.obj_id)
                        else:
                            self.object_delete_requested.emit(self.checklist_id)
                        event.accept()
                        return
        super().keyPressEvent(event)

    def load_objects(self, objects):
        from src.ui.objects.checkbox_widget import CheckboxWidget

        for obj in objects:
            content = json.loads(obj.content)
            text = content.get("text", "")
            if not isinstance(text, str):
                text = str(text)
            widget = CheckboxWidget(
                obj_id=obj.id,
                text=text,
                checked=bool(obj.is_checked),
            )
            widget.changed.connect(self.object_changed)
            widget.delete_requested.connect(self.item_delete_requested)
            self._checkboxes_layout.addWidget(widget)
        self._refresh_size()
