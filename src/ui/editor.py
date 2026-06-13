import json
import os

from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.models.page_object import PageObject
from src.repositories.page_object_repo import PageObjectRepo


class Canvas(QWidget):
    clicked_at = pyqtSignal(int, int)

    _bg_pixmap: QPixmap | None = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._show_photo_bg = False
        if Canvas._bg_pixmap is None:
            bg_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "assets",
                "background",
                "frontpage_bg.png",
            )
            if os.path.exists(bg_path):
                Canvas._bg_pixmap = QPixmap(bg_path)

    def setPhotoBackground(self, show: bool):
        self._show_photo_bg = show
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._show_photo_bg and Canvas._bg_pixmap and not Canvas._bg_pixmap.isNull():
            vp_w, vp_h = self.width(), self.height()
            parent = self.parent()
            while parent:
                if isinstance(parent, QScrollArea):
                    vp_w = parent.viewport().width()
                    vp_h = parent.viewport().height()
                    break
                parent = parent.parent()

            dpr = self.devicePixelRatioF()
            target_w = int(vp_w * dpr)
            target_h = int(vp_h * dpr)
            scaled = Canvas._bg_pixmap.scaled(
                target_w,
                target_h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (vp_w - scaled.width() / dpr) / 2
            y = (vp_h - scaled.height() / dpr) / 2
            painter.drawPixmap(int(x), int(y), scaled)
        else:
            painter.fillRect(self.rect(), QColor("#FFF8F5"))
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked_at.emit(int(event.position().x()), int(event.position().y()))
        event.accept()
        super().mousePressEvent(event)


class ChecklistWidget(QWidget):
    """A container for a group of checkboxes with an add button."""

    object_changed = pyqtSignal(int, bool, str)
    object_delete_requested = pyqtSignal(int)
    item_delete_requested = pyqtSignal(int)

    def __init__(self, checklist_id, page_id=None, parent=None):
        super().__init__(parent)
        self.checklist_id = checklist_id
        self.page_id = page_id
        self._dragging = False
        self._drag_start = None
        self._resizing = False
        self._resize_edge = None
        self._resize_start = None
        self._resize_origin = None
        self._user_width = None
        self._loaded_pos = None
        self._MIN_W = 200
        self._BORDER = 8
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

        from PyQt6.QtWidgets import QLineEdit

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

        from PyQt6.QtWidgets import QToolButton

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
        from src.repositories.page_object_repo import PageObjectRepo

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
            from src.models.page_object import PageObject

            obj = PageObject(
                page_id=self.page_id,
                object_type="checklist_meta",
                content=content,
                sort_order=self.checklist_id * 100 + 50,
            )
            repo.create(obj)

    def _load_meta(self):
        from src.repositories.page_object_repo import PageObjectRepo

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

    def _detect_edge(self, pos):
        b = self._BORDER
        w, h = self.width(), self.height()
        header_h = self._header.height()
        below_header = pos.y() > header_h
        left = below_header and pos.x() < b
        right = below_header and pos.x() > w - b
        top = below_header and pos.y() < header_h + b
        bottom = pos.y() > h - b
        if left and top:
            return "top-left"
        if right and top:
            return "top-right"
        if left and bottom:
            return "bottom-left"
        if right and bottom:
            return "bottom-right"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"
        return None

    def _edge_cursor(self, edge):
        from PyQt6.QtCore import Qt

        cursors = {
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
            "top": Qt.CursorShape.SizeVerCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "top-left": Qt.CursorShape.SizeFDiagCursor,
            "bottom-right": Qt.CursorShape.SizeFDiagCursor,
            "top-right": Qt.CursorShape.SizeBDiagCursor,
            "bottom-left": Qt.CursorShape.SizeBDiagCursor,
        }
        return cursors.get(edge, Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            if pos.y() <= self._header.height():
                child = self._header.childAt(pos)
                if child is self._title_edit:
                    return
                self.setFocus()
                self._dragging = True
                self._drag_start = event.globalPosition().toPoint() - self.pos()
                self._header.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return
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
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_start is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_start
            parent = self.parent()
            if parent:
                new_x = max(0, min(new_pos.x(), parent.width() - self.width()))
                new_y = max(0, min(new_pos.y(), parent.height() - self.height()))
                self.move(new_x, new_y)
            event.accept()
            return
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
                new_h = max(self._MIN_HEADER_H(), oh + dy)
            if "left" in edge:
                new_w = max(self._MIN_W, ow - dx)
                new_x = ox + ow - new_w
            if "top" in edge:
                new_h = max(self._MIN_HEADER_H(), oh - dy)
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
            return
        pos = event.position().toPoint()
        edge = self._detect_edge(pos)
        if edge:
            self.setCursor(self._edge_cursor(edge))
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            self._drag_start = None
            self._header.setCursor(Qt.CursorShape.OpenHandCursor)
            self._save_meta()
            event.accept()
            return
        if self._resizing:
            self._resizing = False
            self._resize_edge = None
            self._resize_start = None
            self._resize_origin = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self._save_meta()
            event.accept()
            return
        super().mouseReleaseEvent(event)

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

    def _MIN_HEADER_H(self):
        return 36 + 42 + 32

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


class TableWidget(QWidget):
    """A floating table card with editable cells."""

    object_changed = pyqtSignal(int, str)
    object_delete_requested = pyqtSignal(int)

    def __init__(self, table_id, page_id=None, parent=None):
        super().__init__(parent)
        self.table_id = table_id
        self.page_id = page_id
        self._dragging = False
        self._drag_start = None
        self._resizing = False
        self._resize_edge = None
        self._resize_start = None
        self._resize_origin = None
        self._user_width = None
        self._loaded_pos = None
        self._MIN_W = 200
        self._MIN_H = 100
        self._BORDER = 8
        self.setObjectName("table_card")
        self.setStyleSheet(
            "#table_card {"
            " background-color: #FFFFFF;"
            " border: 1px solid #F7D1DC;"
            " border-radius: 12px;"
            "}"
            "#table_card > QWidget {"
            " background-color: transparent;"
            "}"
        )
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(36)
        header.setObjectName("table_header")
        header.setCursor(Qt.CursorShape.OpenHandCursor)
        header.setStyleSheet(
            "#table_header {"
            " background-color: #FFF0F3;"
            " border-top-left-radius: 12px;"
            " border-bottom: 1px solid #F7D1DC;"
            "}"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 4, 12, 4)
        header_layout.setSpacing(6)

        from PyQt6.QtWidgets import QLineEdit

        title = QLineEdit("Table")
        title.setPlaceholderText("Table")
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

        from PyQt6.QtWidgets import QPushButton, QToolButton

        add_row_btn = QPushButton("+ Row")
        add_row_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_row_btn.setStyleSheet(
            "QPushButton {"
            " font-size: 10px; color: #CFA6D6; background: transparent;"
            " border: 1px solid #F0E6E8; border-radius: 10px;"
            " padding: 2px 8px; font-family: 'Inter', sans-serif;"
            "}"
            "QPushButton:hover {"
            " background: #FFF0F3; border-color: #CFA6D6; color: #9b59b6;"
            "}"
        )
        add_row_btn.clicked.connect(self._add_row)
        header_layout.addWidget(add_row_btn)

        add_col_btn = QPushButton("+ Col")
        add_col_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_col_btn.setStyleSheet(
            "QPushButton {"
            " font-size: 10px; color: #CFA6D6; background: transparent;"
            " border: 1px solid #F0E6E8; border-radius: 10px;"
            " padding: 2px 8px; font-family: 'Inter', sans-serif;"
            "}"
            "QPushButton:hover {"
            " background: #FFF0F3; border-color: #CFA6D6; color: #9b59b6;"
            "}"
        )
        add_col_btn.clicked.connect(self._add_column)
        header_layout.addWidget(add_col_btn)

        remove_row_btn = QPushButton("- Row")
        remove_row_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_row_btn.setStyleSheet(
            "QPushButton {"
            " font-size: 10px; color: #9CA3AF; background: transparent;"
            " border: 1px solid #F0E6E8; border-radius: 10px;"
            " padding: 2px 8px; font-family: 'Inter', sans-serif;"
            "}"
            "QPushButton:hover {"
            " background: #FFF0F3; border-color: #EF4444; color: #EF4444;"
            "}"
        )
        remove_row_btn.clicked.connect(self._remove_row)
        header_layout.addWidget(remove_row_btn)

        remove_col_btn = QPushButton("- Col")
        remove_col_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_col_btn.setStyleSheet(
            "QPushButton {"
            " font-size: 10px; color: #9CA3AF; background: transparent;"
            " border: 1px solid #F0E6E8; border-radius: 10px;"
            " padding: 2px 8px; font-family: 'Inter', sans-serif;"
            "}"
            "QPushButton:hover {"
            " background: #FFF0F3; border-color: #EF4444; color: #EF4444;"
            "}"
        )
        remove_col_btn.clicked.connect(self._remove_column)
        header_layout.addWidget(remove_col_btn)

        self._row_num_btn = QPushButton("#")
        self._row_num_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._row_num_btn.setCheckable(True)
        self._row_num_btn.setStyleSheet(
            "QPushButton {"
            " font-size: 10px; color: #9CA3AF; background: transparent;"
            " border: 1px solid #F0E6E8; border-radius: 10px;"
            " padding: 2px 8px; font-family: 'Inter', sans-serif;"
            "}"
            "QPushButton:hover {"
            " background: #FFF0F3; border-color: #CFA6D6; color: #CFA6D6;"
            "}"
            "QPushButton:checked {"
            " background: #F3E8F6; border-color: #CFA6D6; color: #CFA6D6;"
            "}"
        )
        self._row_num_btn.clicked.connect(self._toggle_row_numbers)
        header_layout.addWidget(self._row_num_btn)

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
        delete_btn.clicked.connect(self._delete_table)
        header_layout.addWidget(delete_btn)

        self._header = header
        self._layout.addWidget(header)

        from PyQt6.QtWidgets import QTableWidget

        self._table = QTableWidget(2, 3)
        self._table.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionMode(QTableWidget.SelectionMode.ContiguousSelection)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setFixedHeight(28)
        self._table.verticalHeader().setDefaultSectionSize(32)
        self._table.verticalHeader().setMinimumSectionSize(32)
        self._table.verticalHeader().setMaximumSectionSize(32)
        self._table.horizontalHeader().sectionDoubleClicked.connect(self._rename_column)
        self._table.setMinimumHeight(0)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        from PyQt6.QtWidgets import QSizePolicy

        self._table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        for c in range(self._table.columnCount()):
            self._table.horizontalHeader().setSectionResizeMode(
                c, self._table.horizontalHeader().ResizeMode.Stretch
            )
        self._table.setStyleSheet(
            "QTableWidget {"
            " border: none; gridline-color: #F7D1DC;"
            " font-family: 'Inter', sans-serif; font-size: 13px;"
            " color: #2E2B2B; background: #FFFFFF;"
            " selection-background-color: #F3E8F6;"
            " selection-color: #2E2B2B;"
            "}"
            "QTableWidget::item {"
            " padding: 4px 8px; border: none;"
            " border-radius: 6px;"
            "}"
            "QTableWidget::item:selected {"
            " background: #F3E8F6; color: #2E2B2B;"
            "}"
            "QTableWidget QHeaderView::section {"
            " background: #FFF0F3; border: none;"
            " border-bottom: 1px solid #F7D1DC;"
            " border-right: 1px solid #F7D1DC;"
            " padding: 4px 8px;"
            " font-family: 'Inter', sans-serif; font-size: 11px;"
            " font-weight: 600; color: #8B6B7B;"
            "}"
            "QTableWidget QTableCornerButton::section {"
            " background: #FFF0F3; border: none;"
            " border-bottom: 1px solid #F7D1DC;"
            " border-right: 1px solid #F7D1DC;"
            "}"
            "QTableWidget QLineEdit {"
            " border: 1px solid #CFA6D6; border-radius: 6px;"
            " padding: 4px 8px; font-family: 'Inter', sans-serif;"
            " font-size: 13px; color: #2E2B2B; background: #FFFFFF;"
            "}"
            "QTableWidget QLineEdit:focus {"
            " border-color: #9b59b6;"
            "}"
            "QScrollBar:vertical {"
            " background: #FFFFFF; width: 8px; margin: 0; }"
            "QScrollBar::handle:vertical {"
            " background: #E8DDE0; border-radius: 4px; min-height: 20px; }"
            "QScrollBar::handle:vertical:hover {"
            " background: #CFA6D6; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {"
            " height: 0; }"
            "QScrollBar:horizontal {"
            " background: #FFFFFF; height: 8px; margin: 0; }"
            "QScrollBar::handle:horizontal {"
            " background: #E8DDE0; border-radius: 4px; min-width: 20px; }"
            "QScrollBar::handle:horizontal:hover {"
            " background: #CFA6D6; }"
            "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {"
            " width: 0; }"
        )
        self._table.cellChanged.connect(self._on_cell_changed)
        self._layout.addWidget(self._table)

        self._install_border_filter()

    def sizeHint(self):
        from PyQt6.QtCore import QSize

        header_h = 36
        table_header_h = 28
        rows = self._table.rowCount()
        row_h = 32
        total_h = header_h + table_header_h + (rows * row_h)
        return QSize(self.width(), total_h)

    def _on_title_changed(self):
        self._save_meta()

    def _on_cell_changed(self, row, col):
        self._save_meta()

    def _add_row(self):
        self._table.insertRow(self._table.rowCount())

    def _add_column(self):
        from PyQt6.QtWidgets import QTableWidgetItem

        col = self._table.columnCount()
        self._table.setColumnCount(col + 1)
        self._table.setHorizontalHeaderItem(col, QTableWidgetItem(f"Column {col + 1}"))
        self._table.horizontalHeader().setSectionResizeMode(
            col, self._table.horizontalHeader().ResizeMode.Stretch
        )

    def _remove_row(self):
        rows = self._table.selectionModel().selectedRows()
        if rows:
            for row in sorted(rows, reverse=True):
                self._table.removeRow(row.row())
        elif self._table.rowCount() > 1:
            self._table.removeRow(self._table.rowCount() - 1)
        self._save_meta()

    def _remove_column(self):
        cols = self._table.selectionModel().selectedColumns()
        if cols:
            for col in sorted(cols, reverse=True):
                self._table.removeColumn(col.column())
        elif self._table.columnCount() > 1:
            self._table.removeColumn(self._table.columnCount() - 1)
        self._save_meta()

    def _toggle_row_numbers(self):
        show = self._row_num_btn.isChecked()
        self._table.verticalHeader().setVisible(show)
        self._save_meta()

    def _rename_column(self, logical_index):
        from PyQt6.QtWidgets import QLineEdit

        current = self._table.horizontalHeaderItem(logical_index)
        current_text = current.text() if current else ""

        header = self._table.horizontalHeader()
        x = header.sectionPosition(logical_index)
        w = header.sectionSize(logical_index)
        h = header.height()

        edit = QLineEdit(self._table.viewport())
        edit.setText(current_text)
        edit.setGeometry(x, 0, w, h)
        edit.setStyleSheet(
            "QLineEdit { border: 1px solid #CFA6D6; border-radius: 4px;"
            " padding: 2px 4px; font-family: 'Inter', sans-serif;"
            " font-size: 11px; font-weight: 600; color: #8B6B7B;"
            " background: #FFFFFF; }"
        )
        edit.setFocus()
        edit.selectAll()
        self._header_edit = edit
        edit.show()

        def finish_edit():
            if self._header_edit is not edit:
                return
            new_text = edit.text().strip()
            if new_text:
                self._table.horizontalHeaderItem(logical_index).setText(new_text)
                self._save_meta()
            edit.deleteLater()
            self._header_edit = None

        edit.editingFinished.connect(finish_edit)

    def _delete_table(self):
        self.object_delete_requested.emit(self.table_id)

    def _install_border_filter(self):
        self._table.setMouseTracking(True)
        self._table.viewport().installEventFilter(self)
        self._table.installEventFilter(self)

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent, QMouseEvent

        if obj not in (self._table, self._table.viewport()):
            return super().eventFilter(obj, event)

        if isinstance(event, QKeyEvent):
            if event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_Tab:
                    self._handle_tab(event)
                    return True
                if event.key() == Qt.Key.Key_Backtab:
                    self._handle_tab(event, reverse=True)
                    return True
            return super().eventFilter(obj, event)

        if not isinstance(event, QMouseEvent):
            return super().eventFilter(obj, event)

        pos = self._table.viewport().mapTo(self, event.position().toPoint())

        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
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
                    new_h = max(self._MIN_H, oh + dy)
                if "left" in edge:
                    new_w = max(self._MIN_W, ow - dx)
                    new_x = ox + ow - new_w
                if "top" in edge:
                    new_h = max(self._MIN_H, oh - dy)
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
            else:
                edge = self._detect_edge(pos)
                if edge and not self._resizing and not self._dragging:
                    self.setCursor(self._edge_cursor(edge))
                elif not edge and not self._resizing and not self._dragging:
                    self.setCursor(Qt.CursorShape.ArrowCursor)

        if event.type() == QEvent.Type.MouseButtonRelease:
            if self._resizing:
                self._resizing = False
                self._resize_edge = None
                self._resize_start = None
                self._resize_origin = None
                self.setCursor(Qt.CursorShape.ArrowCursor)
                self._save_meta()
                event.accept()
                return True

        return super().eventFilter(obj, event)

    def _handle_tab(self, event, reverse=False):
        row = self._table.currentRow()
        col = self._table.currentColumn()
        rows = self._table.rowCount()
        cols = self._table.columnCount()

        if reverse:
            col -= 1
            if col < 0:
                col = cols - 1
                row -= 1
                if row < 0:
                    row = rows - 1
        else:
            col += 1
            if col >= cols:
                col = 0
                row += 1
                if row >= rows:
                    self._table.insertRow(rows)
                    self._save_meta()

        self._table.setCurrentCell(row, col)

    def _save_meta(self):
        from src.repositories.page_object_repo import PageObjectRepo

        repo = PageObjectRepo()
        meta = repo.get_table_meta(self.page_id, self.table_id)
        rows = self._table.rowCount()
        cols = self._table.columnCount()
        headers = [
            self._table.horizontalHeaderItem(c).text()
            if self._table.horizontalHeaderItem(c)
            else ""
            for c in range(cols)
        ]
        data = []
        for r in range(rows):
            row_data = []
            for c in range(cols):
                item = self._table.item(r, c)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        content = json.dumps(
            {
                "x": self.x(),
                "y": self.y(),
                "width": self.width(),
                "title": self._title_edit.text(),
                "headers": headers,
                "data": data,
                "show_row_numbers": self._row_num_btn.isChecked(),
            }
        )
        if meta:
            meta.content = content
            repo.update(meta)
        else:
            from src.models.page_object import PageObject

            obj = PageObject(
                page_id=self.page_id,
                object_type="table_meta",
                content=content,
                sort_order=self.table_id * 100 + 50,
            )
            repo.create(obj)

    def _load_meta(self):
        from src.repositories.page_object_repo import PageObjectRepo

        meta = PageObjectRepo().get_table_meta(self.page_id, self.table_id)
        if meta:
            data = json.loads(meta.content)
            self._user_width = data.get("width")
            title = data.get("title", "Table")
            self._title_edit.setText(title)
            headers = data.get("headers", ["Column 1", "Column 2", "Column 3"])
            rows_data = data.get("data", [["", "", ""], ["", "", ""]])
            self._table.setColumnCount(len(headers))
            self._table.setHorizontalHeaderLabels(headers)
            self._table.setRowCount(len(rows_data))
            from PyQt6.QtWidgets import QTableWidgetItem

            for r, row in enumerate(rows_data):
                for c, val in enumerate(row):
                    self._table.setItem(r, c, QTableWidgetItem(val))
            show_row_nums = data.get("show_row_numbers", False)
            self._row_num_btn.setChecked(show_row_nums)
            self._table.verticalHeader().setVisible(show_row_nums)
            x = data.get("x")
            y = data.get("y")
            if x is not None and y is not None:
                self._loaded_pos = (x, y)
                self.move(x, y)
            else:
                self._loaded_pos = None
        else:
            self._loaded_pos = None

    def _MIN_HEADER_H(self):
        return 36 + 42

    def _detect_edge(self, pos):
        b = self._BORDER
        w, h = self.width(), self.height()
        header_h = self._header.height()
        below_header = pos.y() > header_h
        left = below_header and pos.x() < b
        right = below_header and pos.x() > w - b
        top = below_header and pos.y() < header_h + b
        bottom = pos.y() > h - b
        if left and top:
            return "top-left"
        if right and top:
            return "top-right"
        if left and bottom:
            return "bottom-left"
        if right and bottom:
            return "bottom-right"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"
        return None

    def _edge_cursor(self, edge):
        cursors = {
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
            "top": Qt.CursorShape.SizeVerCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "top-left": Qt.CursorShape.SizeFDiagCursor,
            "bottom-right": Qt.CursorShape.SizeFDiagCursor,
            "top-right": Qt.CursorShape.SizeBDiagCursor,
            "bottom-left": Qt.CursorShape.SizeBDiagCursor,
        }
        return cursors.get(edge, Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            if pos.y() <= self._header.height():
                child = self._header.childAt(pos)
                if child is self._title_edit:
                    return
                self.setFocus()
                self._dragging = True
                self._drag_start = event.globalPosition().toPoint() - self.pos()
                self._header.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return
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
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_start is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_start
            parent = self.parent()
            if parent:
                new_x = max(0, min(new_pos.x(), parent.width() - self.width()))
                new_y = max(0, min(new_pos.y(), parent.height() - self.height()))
                self.move(new_x, new_y)
            event.accept()
            return
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
                new_h = max(self._MIN_H, oh + dy)
            if "left" in edge:
                new_w = max(self._MIN_W, ow - dx)
                new_x = ox + ow - new_w
            if "top" in edge:
                new_h = max(self._MIN_H, oh - dy)
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
            return
        pos = event.position().toPoint()
        edge = self._detect_edge(pos)
        if edge:
            self.setCursor(self._edge_cursor(edge))
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            self._drag_start = None
            self._header.setCursor(Qt.CursorShape.OpenHandCursor)
            self._save_meta()
            event.accept()
            return
        if self._resizing:
            self._resizing = False
            self._resize_edge = None
            self._resize_start = None
            self._resize_origin = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self._save_meta()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class PageEditor(QWidget):
    navigate_to_page = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page_id = None
        self._empty_hint = None
        self._toc_widget = None
        self._parent_folder_id = None
        self._objects = []
        self._checklists = {}
        self._tables = {}
        self._canvas_click_pos = None
        self.setStyleSheet("background: #2a1a35;")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._build_toolbar(main_layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: #2a1a35; }")

        self.content = Canvas()
        self.content.clicked_at.connect(self._on_canvas_clicked)
        self.scroll.setWidget(self.content)
        self.scroll.viewport().installEventFilter(self)
        self.scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self.content.setPhotoBackground(True)

        self.welcome_label = QLabel()
        self.welcome_label.setWordWrap(True)
        self.welcome_label.setObjectName("welcome_title")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("""
            font-family: 'Magnolia', cursive;
            font-size: 80px;
            color: #F0E4F5;
            background: transparent;
            padding: 40px;
        """)
        self.welcome_label.setTextFormat(Qt.TextFormat.RichText)
        self.welcome_label.setText(
            "Hello, lovely!<br>Let's make it a productive day!"
            ' <span style="font-size:35px;">❤️</span>'
        )
        self.welcome_label.setParent(self.content)
        self.welcome_label.adjustSize()
        self.welcome_label.show()

        self._page_empty_hint = QLabel("Click + buttons to add your first object")
        self._page_empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_empty_hint.setStyleSheet(
            "font-family: 'Inter', sans-serif;"
            " font-size: 14px; color: #9CA3AF;"
            " font-style: italic;"
            " background: transparent;"
        )
        self._page_empty_hint.setParent(self.content)
        self._page_empty_hint.hide()

        self._build_floating_add_button()

        main_layout.addWidget(self.scroll, 1)

    def _build_floating_add_button(self):
        self._add_btn = QPushButton("+", self.content)
        self._add_btn.setFixedSize(48, 48)
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.setStyleSheet(
            "QPushButton {"
            " font-size: 24px; font-weight: 300;"
            " color: #FFFFFF; background: #CFA6D6;"
            " border: none; border-radius: 24px;"
            "}"
            "QPushButton:hover {"
            " background: #B894C0;"
            "}"
        )
        self._add_btn.clicked.connect(self._show_add_menu)
        self._add_btn.hide()

    def _show_add_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu {"
            " background: #FFFFFF; border: 1px solid #F7D1DC;"
            " border-radius: 8px; padding: 4px;"
            " font-family: 'Inter', sans-serif; font-size: 13px;"
            "}"
            "QMenu::item {"
            " padding: 8px 20px; border-radius: 6px;"
            "}"
            "QMenu::item:selected {"
            " background: #FFF0F3; color: #2E2B2B;"
            "}"
        )
        checkbox_action = menu.addAction("✓  Checklist")
        table_action = menu.addAction("⊞  Table")
        action = menu.exec(self._add_btn.mapToGlobal(self._add_btn.rect().bottomLeft()))
        if action == checkbox_action:
            self._add_checklist()
        elif action == table_action:
            self._add_table()

    def _center_welcome_label(self):
        if hasattr(self, "welcome_label") and self.welcome_label.isVisible():
            canvas_width = self.content.width()
            canvas_height = self.content.height()
            label_width = self.welcome_label.width()
            label_height = self.welcome_label.height()
            x = (canvas_width - label_width) // 2
            y = (canvas_height - label_height) // 10
            self.welcome_label.move(x, y)

    def eventFilter(self, obj, event):
        if obj is self.scroll.viewport() and event.type() == QEvent.Type.Resize:
            if self.current_page_id is None:
                vp = self.scroll.viewport()
                self.content.setFixedWidth(vp.width())
                self.content.resize(vp.width(), vp.height())
            self._center_welcome_label()
            self._center_empty_hint()
            self._position_floating_button()
        return super().eventFilter(obj, event)

    def _on_scroll(self, value):
        pass

    def _build_toolbar(self, parent_layout):
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet(
            "background: #FFF8F5; border-bottom: 1px solid #F0E6E8;"
        )

        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(12, 6, 12, 6)

        self.page_title = QLabel("Select a page")
        self.page_title.setObjectName("page_title")
        self.page_title.setStyleSheet(
            "font-size: 18px; font-weight: 600; padding: 4px 8px;"
            " color: #2E2B2B; font-family: 'Playfair Display', serif;"
        )
        toolbar.addWidget(self.page_title)
        toolbar.addStretch()

        self._back_btn = QPushButton("← Back to folder")
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.setStyleSheet(
            "QPushButton {"
            " font-size: 12px; color: #CFA6D6; background: transparent;"
            " border: 1px solid #F0E6E8; border-radius: 14px;"
            " padding: 4px 14px; font-family: 'Inter', sans-serif;"
            "}"
            "QPushButton:hover {"
            " background: #FFF0F3; border-color: #CFA6D6;"
            " color: #9b59b6;"
            "}"
        )
        self._back_btn.clicked.connect(self._on_back_clicked)
        self._back_btn.hide()
        toolbar.addWidget(self._back_btn)

        self._checkbox_btn = QPushButton("✓ + Checklist")
        self._checkbox_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checkbox_btn.setStyleSheet(
            "QPushButton {"
            " font-size: 12px; color: #CFA6D6; background: transparent;"
            " border: 1px solid #F0E6E8; border-radius: 14px;"
            " padding: 4px 14px; font-family: 'Inter', sans-serif;"
            "}"
            "QPushButton:hover {"
            " background: #FFF0F3; border-color: #CFA6D6;"
            " color: #9b59b6;"
            "}"
        )
        self._checkbox_btn.clicked.connect(self._add_checklist)
        self._checkbox_btn.hide()
        toolbar.addWidget(self._checkbox_btn)

        self._table_btn = QPushButton("⊞ + Table")
        self._table_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._table_btn.setStyleSheet(
            "QPushButton {"
            " font-size: 12px; color: #CFA6D6; background: transparent;"
            " border: 1px solid #F0E6E8; border-radius: 14px;"
            " padding: 4px 14px; font-family: 'Inter', sans-serif;"
            "}"
            "QPushButton:hover {"
            " background: #FFF0F3; border-color: #CFA6D6;"
            " color: #9b59b6;"
            "}"
        )
        self._table_btn.clicked.connect(self._add_table)
        self._table_btn.hide()
        toolbar.addWidget(self._table_btn)

        parent_layout.addWidget(toolbar_widget)

    def _on_canvas_clicked(self, x, y):
        self._canvas_click_pos = (x, y)

    def _on_back_clicked(self):
        if self._parent_folder_id is not None:
            self.navigate_to_page.emit(self._parent_folder_id)

    def _center_empty_hint(self):
        if self._page_empty_hint.isVisible():
            canvas_width = self.content.width()
            hint_width = self._page_empty_hint.width()
            x = (canvas_width - hint_width) // 2
            y = 120
            self._page_empty_hint.move(x, y)

    def _position_floating_button(self):
        if hasattr(self, "_add_btn") and self._add_btn.isVisible():
            canvas_w = self.content.width()
            canvas_h = self.content.height()
            self._add_btn.move(canvas_w - 70, canvas_h - 70)

    def load_page(self, page_id: int):
        from src.repositories.page_repo import PageRepo

        self.current_page_id = page_id
        self._clear_toc()
        self._clear_objects()
        page = PageRepo().get_by_id(page_id)
        if page:
            self.page_title.setText(page.title)
            if page.parent_id is not None:
                self._parent_folder_id = page.parent_id
                self._back_btn.show()
            else:
                self._parent_folder_id = None
                self._back_btn.hide()
        else:
            self._parent_folder_id = None
            self._back_btn.hide()
        if self._empty_hint:
            self._empty_hint.hide()
        self.welcome_label.hide()
        self.content.setPhotoBackground(False)

        if page and page.page_type == "folder":
            children = PageRepo().get_children(page_id)
            if children:
                self._page_empty_hint.hide()
                self._show_toc(children)
            else:
                self._page_empty_hint.hide()
            self._checkbox_btn.hide()
            self._table_btn.hide()
            self._add_btn.hide()
        else:
            self._load_objects()
            self._checkbox_btn.show()
            self._table_btn.show()
            self._add_btn.show()
            self._position_floating_button()
            if not self._objects:
                self._page_empty_hint.show()
                self._center_empty_hint()
            else:
                self._page_empty_hint.hide()

    def _load_objects(self):
        if not self.current_page_id:
            return
        self._objects = PageObjectRepo().get_by_page(self.current_page_id)
        if not self._objects:
            return
        self._group_objects_into_checklists()
        self._group_objects_into_tables()

    def _group_objects_into_checklists(self):
        checklists = {}
        for obj in self._objects:
            if obj.object_type in ("checklist_meta", "table_meta"):
                continue
            cid = obj.sort_order // 100
            if cid not in checklists:
                checklists[cid] = []
            checklists[cid].append(obj)

        for cid, objs in sorted(checklists.items()):
            self._create_checklist_widget(cid, objs)

    def _group_objects_into_tables(self):
        table_ids = set()
        for obj in self._objects:
            if obj.object_type == "table_meta":
                table_id = obj.sort_order // 100
                table_ids.add(table_id)

        for table_id in sorted(table_ids):
            self._create_table_widget(table_id)

    def _create_checklist_widget(self, checklist_id, objects=None):
        widget = ChecklistWidget(
            checklist_id, page_id=self.current_page_id, parent=self.content
        )
        widget.object_changed.connect(self._on_object_changed)
        widget.object_delete_requested.connect(self._on_checklist_delete)
        widget.item_delete_requested.connect(self._on_item_delete)
        if objects:
            widget.load_objects(objects)
        self._checklists[checklist_id] = widget

        canvas_w = self.content.width()
        container_w = min(400, canvas_w - 80)
        widget.setFixedWidth(container_w)
        widget._load_meta()
        if not widget._user_width:
            widget._user_width = container_w
        widget._refresh_size()
        if not widget._loaded_pos:
            x = (canvas_w - container_w) // 2
            y = 60 + len(self._checklists) * 200
            widget.move(x, y)
        widget.show()
        return widget

    def _add_checklist(self):
        if not self.current_page_id:
            return

        checklist_id = max(self._checklists.keys(), default=-1) + 1
        widget = self._create_checklist_widget(checklist_id)

        if self._canvas_click_pos:
            x, y = self._canvas_click_pos
            canvas_w = self.content.width()
            container_w = min(400, canvas_w - 80)
            widget.move(max(20, x - container_w // 2), max(60, y - 30))
            self._canvas_click_pos = None

        item_widget = widget._add_item()
        obj = PageObjectRepo().get_by_id(item_widget.obj_id)
        self._objects.append(obj)
        self._page_empty_hint.hide()
        self._position_floating_button()

    def _add_table(self):
        if not self.current_page_id:
            return

        table_id = max(self._tables.keys(), default=-1) + 1
        widget = self._create_table_widget(table_id)

        if self._canvas_click_pos:
            x, y = self._canvas_click_pos
            canvas_w = self.content.width()
            container_w = min(400, canvas_w - 80)
            widget.move(max(20, x - container_w // 2), max(60, y - 30))
            self._canvas_click_pos = None

        widget._save_meta()
        self._page_empty_hint.hide()
        self._position_floating_button()

    def _create_table_widget(self, table_id):
        widget = TableWidget(
            table_id, page_id=self.current_page_id, parent=self.content
        )
        widget.object_delete_requested.connect(self._on_table_delete)
        self._tables[table_id] = widget

        canvas_w = self.content.width()
        container_w = min(400, canvas_w - 80)
        widget.setFixedWidth(container_w)
        widget._load_meta()
        if not widget._user_width:
            widget._user_width = container_w
        x = (canvas_w - container_w) // 2
        y = 60 + len(self._checklists) * 200 + len(self._tables) * 200
        widget.move(x, y)
        widget.show()
        return widget

    def _on_table_delete(self, table_id):
        if table_id in self._tables:
            widget = self._tables[table_id]
            widget.hide()
            widget.deleteLater()
            del self._tables[table_id]
        meta = PageObjectRepo().get_table_meta(self.current_page_id, table_id)
        if meta:
            PageObjectRepo().delete(meta.id)
        self._objects = [
            o
            for o in self._objects
            if not (o.object_type == "table_meta" and o.sort_order // 100 == table_id)
        ]
        if not self._objects:
            self._page_empty_hint.show()
            self._center_empty_hint()

    def _on_object_changed(self, obj_id, checked, text):
        for obj in self._objects:
            if obj.id == obj_id:
                obj.is_checked = checked
                obj.content = json.dumps({"text": text, "checked": checked})
                PageObjectRepo().update(obj)
                break

    def _on_checklist_delete(self, checklist_id):
        if checklist_id in self._checklists:
            del self._checklists[checklist_id]
        self._objects = [
            o for o in self._objects if o.sort_order // 100 != checklist_id
        ]
        if not self._objects:
            self._page_empty_hint.show()
            self._center_empty_hint()

    def _on_item_delete(self, obj_id):
        PageObjectRepo().delete(obj_id)
        self._objects = [o for o in self._objects if o.id != obj_id]
        for cid, checklist in list(self._checklists.items()):
            for i in range(checklist._checkboxes_layout.count()):
                w = checklist._checkboxes_layout.itemAt(i).widget()
                if w and hasattr(w, "obj_id") and w.obj_id == obj_id:
                    checklist._checkboxes_layout.removeWidget(w)
                    w.deleteLater()
                    break
            checklist._refresh_size()
            if checklist._checkboxes_layout.count() == 0:
                self._objects = [o for o in self._objects if o.sort_order // 100 != cid]
                del self._checklists[cid]
                checklist.deleteLater()
        if not self._objects:
            self._page_empty_hint.show()
            self._center_empty_hint()

    def _clear_objects(self):
        self._objects = []
        for widget in self._checklists.values():
            widget.hide()
            widget.deleteLater()
        self._checklists.clear()
        for widget in self._tables.values():
            widget.hide()
            widget.deleteLater()
        self._tables.clear()

    def _show_toc(self, children):
        from PyQt6.QtWidgets import QPushButton

        toc_container = QWidget(self.content)
        toc_container.setStyleSheet("background: transparent;")
        toc_layout = QVBoxLayout(toc_container)
        toc_layout.setContentsMargins(40, 40, 40, 40)
        toc_layout.setSpacing(6)

        folder_label = QLabel("Pages in this folder")
        folder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        folder_label.setStyleSheet(
            "font-family: 'Playfair Display', serif;"
            " font-size: 24px; font-weight: 600;"
            " color: #9b59b6; background: transparent;"
            " padding: 8px 0 16px 0;"
        )
        toc_layout.addWidget(folder_label)

        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background: #F0E6E8;")
        toc_layout.addWidget(separator)
        toc_layout.addSpacing(8)

        for child in children:
            btn = QPushButton(f"  {child.title}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton {"
                " text-align: left; font-size: 15px;"
                " color: #CFA6D6; background: transparent;"
                " border: 1px solid transparent; padding: 10px 16px;"
                " border-radius: 8px;"
                " font-family: 'Inter', sans-serif;"
                "}"
                "QPushButton:hover {"
                " background: #FFF0F3; border-color: #F7D1DC;"
                " color: #9b59b6;"
                "}"
            )
            btn.clicked.connect(
                lambda checked, pid=child.id: self.navigate_to_page.emit(pid)
            )
            toc_layout.addWidget(btn)

        toc_layout.addStretch()
        toc_container.adjustSize()

        canvas_width = self.content.width()
        toc_width = toc_container.sizeHint().width()
        x = (canvas_width - toc_width) // 2
        toc_container.move(x, 60)
        toc_container.show()
        self._toc_widget = toc_container

    def _clear_toc(self):
        if self._toc_widget:
            self._toc_widget.deleteLater()
            self._toc_widget = None

    def keyPressEvent(self, event):
        is_delete_key = event.key() == Qt.Key.Key_Delete
        is_ctrl_d = (
            event.key() == Qt.Key.Key_D
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        )
        if is_delete_key or is_ctrl_d:
            from PyQt6.QtWidgets import QApplication

            focused = QApplication.focusWidget()
            if not focused:
                return
            for checklist in self._checklists.values():
                if checklist.isAncestorOf(focused):
                    event.accept()
                    return
        super().keyPressEvent(event)

    def clear_editor(self):
        self.current_page_id = None
        self.page_title.setText("Select a page")
        self.welcome_label.show()
        self._page_empty_hint.hide()
        self._clear_toc()
        self._clear_objects()
        self._back_btn.hide()
        self._checkbox_btn.hide()
        self._table_btn.hide()
        self._add_btn.hide()
        self._parent_folder_id = None
        self._canvas_click_pos = None
        self.content.setPhotoBackground(True)
        self._center_welcome_label()

    def save_current(self):
        pass
