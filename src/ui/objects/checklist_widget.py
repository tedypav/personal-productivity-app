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

from src.controllers.checklist_controller import ChecklistController
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
        self._checklist_controller = ChecklistController()
        self.setObjectName("checklist")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(36)
        header.setObjectName("checklistHeader")
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header.setCursor(Qt.CursorShape.OpenHandCursor)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 4, 12, 4)
        header_layout.setSpacing(6)

        title = QLineEdit("Checklist")
        title.setObjectName("checklistTitle")
        title.setPlaceholderText("Checklist")
        title.returnPressed.connect(self._on_title_changed)
        title.editingFinished.connect(self._on_title_changed)
        self._title_edit = title
        header_layout.addWidget(title)
        header_layout.addStretch()

        delete_btn = QToolButton()
        delete_btn.setObjectName("checklistDeleteBtn")
        delete_btn.setText("×")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(self._delete_checklist)
        header_layout.addWidget(delete_btn)
        self._delete_btn = delete_btn

        self._header = header
        self._layout.addWidget(header)

        self._checkboxes_layout = QVBoxLayout()
        self._checkboxes_layout.setContentsMargins(0, 0, 0, 0)
        self._checkboxes_layout.setSpacing(6)
        self._layout.addLayout(self._checkboxes_layout)

        add_btn = QPushButton("+ Add item")
        add_btn.setObjectName("checklistAddBtn")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
                if pos.y() <= self._header.height():
                    child = self._header.childAt(pos)
                    if child is self._title_edit:
                        return False
                    if child is self._delete_btn:
                        return False
                    self.setFocus()
                    self._dragging = True
                    self._drag_start = event.globalPosition().toPoint() - self.pos()
                    self._header.setCursor(Qt.CursorShape.ClosedHandCursor)
                    event.accept()
                    return True
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
        if event.type() == QEvent.Type.MouseButtonRelease:
            if self._dragging:
                self._dragging = False
                self._drag_start = None
                self._header.setCursor(Qt.CursorShape.OpenHandCursor)
                self._save_meta()
                event.accept()
                return True
            if self._resizing:
                self._resizing = False
                self._resize_edge = None
                self._resize_start = None
                self._resize_origin = None
                self.setCursor(Qt.CursorShape.ArrowCursor)
                self._on_resize_complete()
                self._save_meta()
                event.accept()
                return True
        if event.type() == QEvent.Type.MouseMove:
            if self._dragging and self._drag_start is not None:
                curr = event.globalPosition().toPoint()
                new_pos = curr - self._drag_start
                parent = self.parent()
                if parent:
                    new_x = max(0, min(new_pos.x(), parent.width() - self.width()))
                    new_y = max(0, min(new_pos.y(), parent.height() - self.height()))
                    self.move(new_x, new_y)
                event.accept()
                return True
            if self._resizing and self._resize_start is not None:
                curr = event.globalPosition().toPoint()
                dx = curr.x() - self._resize_start.x()
                dy = curr.y() - self._resize_start.y()
                ox, oy, ow, oh = self._resize_origin
                edge = self._resize_edge
                new_x, new_y, new_w, new_h = ox, oy, ow, oh
                if "right" in edge:
                    new_w = max(self._MIN_W, ow + dx)
                if "bottom" in edge:
                    new_h = max(self._min_height(), oh + dy)
                if "left" in edge:
                    new_w = max(self._MIN_W, ow - dx)
                    new_x = ox + ow - new_w
                if "top" in edge:
                    new_h = max(self._min_height(), oh - dy)
                    new_y = oy + oh - new_h
                parent = self.parent()
                if parent:
                    new_x = max(0, min(new_x, parent.width() - new_w))
                    new_y = max(0, min(new_y, parent.height() - new_h))
                self._user_width = new_w
                self.setMinimumWidth(0)
                self.setMaximumWidth(16777215)
                self.setGeometry(new_x, new_y, new_w, new_h)
                event.accept()
                return True
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
                "height": self.height(),
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
            try:
                data = json.loads(meta.content)
            except (json.JSONDecodeError, ValueError):
                self._loaded_pos = None
                return
            self._user_width = data.get("width")
            self._user_height = data.get("height")
            title = data.get("title", "Checklist")
            self._title_edit.setText(title)
            x = data.get("x")
            y = data.get("y")
            if x is not None and y is not None:
                self._loaded_pos = (x, y)
                self.move(x, y)
            else:
                self._loaded_pos = None
            if self._user_width:
                self.resize(self._user_width, self._user_height or self.height())
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
        pass

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
            try:
                content = json.loads(obj.content)
            except (json.JSONDecodeError, ValueError):
                content = {}
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
