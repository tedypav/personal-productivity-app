from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QIcon, QImage, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.controllers.textbox_controller import TextboxController
from src.ui.objects.checkbox_widget import CustomCheckBox
from src.ui.objects.resizable_mixin import ResizableMixin

__all__ = ["TextboxWidget"]


# ── Text Block ──────────────────────────────────────────────────────


class TextboxTextBlock(QWidget):
    """A rich-text block: click to edit, drag bottom handle to resize."""

    content_changed = pyqtSignal()
    delete_requested = pyqtSignal()

    def __init__(self, html: str = "", parent=None):
        super().__init__(parent)
        self._html = html
        self._editing = False
        self._resizing = False
        self._resize_start = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 4, 0)
        header_row.addStretch()
        del_btn = QPushButton("✕ Remove")
        del_btn.setObjectName("textboxTableBtn")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(self.delete_requested.emit)
        header_row.addWidget(del_btn)
        header_row.addWidget(del_btn)
        self._layout.addLayout(header_row)

        self._editor = QTextEdit()
        self._editor.setObjectName("textboxEditor")
        self._editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._editor.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self._editor.textChanged.connect(self._on_text_changed)
        self._editor.viewport().installEventFilter(self)
        self._layout.addWidget(self._editor)

        self._handle = QWidget()
        self._handle.setFixedHeight(6)
        self._handle.setCursor(Qt.CursorShape.SizeVerCursor)
        self._handle.setObjectName("textboxResizeHandle")
        self._handle.installEventFilter(self)
        self._layout.addWidget(self._handle)

        self._apply_view_mode()

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QMouseEvent

        if obj is self._editor.viewport():
            if (
                event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton
                and not self._editing
            ):
                self._enter_edit_mode()
            return super().eventFilter(obj, event)

        if obj is self._handle and isinstance(event, QMouseEvent):
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self._resizing = True
                    self._resize_start = event.globalPosition().toPoint()
                    event.accept()
                    return True
            if event.type() == QEvent.Type.MouseMove:
                if self._resizing and self._resize_start is not None:
                    curr = event.globalPosition().toPoint()
                    dy = curr.y() - self._resize_start.y()
                    new_h = max(30, self.height() + dy)
                    self._resize_start = curr
                    self._editor.setMinimumHeight(max(30, new_h - 6))
                    event.accept()
                    return True
            if event.type() == QEvent.Type.MouseButtonRelease:
                if self._resizing:
                    self._resizing = False
                    self._resize_start = None
                    event.accept()
                    return True

        return super().eventFilter(obj, event)

    def _enter_edit_mode(self):
        self._editing = True
        self._editor.setReadOnly(False)
        if not self._html.strip():
            self._editor.clear()
        self._editor.setFocus()

    def exit_edit_mode(self):
        if self._editing:
            self._editing = False
            self._html = self._editor.toHtml()
            self._apply_view_mode()
            self.content_changed.emit()

    def _apply_view_mode(self):
        self._editor.setReadOnly(True)
        if self._html.strip():
            self._editor.setHtml(self._html)
        else:
            self._editor.setHtml(
                '<p style="color:#9CA3AF; font-style:italic;">'
                "Double-click to start typing...</p>"
            )
        self._editor.setMinimumHeight(0)

    def _on_text_changed(self):
        if self._editing:
            self._html = self._editor.toHtml()

    def get_content(self) -> str:
        return self._html

    def set_content(self, html: str):
        self._html = html
        self._apply_view_mode()

    def text_cursor(self):
        if self._editing:
            return self._editor.textCursor()
        return None


# ── Checklist Block ─────────────────────────────────────────────────


class TextboxChecklistItem(QWidget):
    """A single checkbox row inside a textbox checklist block."""

    changed = pyqtSignal()
    delete_requested = pyqtSignal()

    def __init__(self, text: str = "", checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        self._checkbox = CustomCheckBox(checked=checked)
        self._checkbox.stateChanged.connect(self._on_check)
        layout.addWidget(self._checkbox)

        self._text = QLineEdit(text)
        self._text.setObjectName("textboxChecklistText")
        self._text.setPlaceholderText("Type something...")
        self._text.textChanged.connect(lambda: self.changed.emit())
        layout.addWidget(self._text, 1)

        delete_btn = QToolButton()
        delete_btn.setText("×")
        delete_btn.setObjectName("textboxDeleteBtn")
        delete_btn.setFixedSize(22, 22)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(self.delete_requested.emit)
        layout.addWidget(delete_btn)

    def _on_check(self, state):
        self._checked = state == Qt.CheckState.Checked.value
        self.changed.emit()

    def get_data(self) -> dict:
        return {"text": self._text.text(), "checked": self._checked}

    def set_data(self, data: dict):
        self._checkbox.setChecked(data.get("checked", False))
        self._text.setText(data.get("text", ""))


class TextboxChecklistBlock(QWidget):
    """An inline checklist block with checkboxes."""

    content_changed = pyqtSignal()
    delete_requested = pyqtSignal()

    def __init__(self, items: list | None = None, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(8, 4, 4, 0)
        header_row.addStretch()
        del_btn = QPushButton("✕ Remove")
        del_btn.setObjectName("textboxTableBtn")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(self.delete_requested.emit)
        header_row.addWidget(del_btn)
        self._layout.addLayout(header_row)

        self._items_layout = QVBoxLayout()
        self._items_layout.setContentsMargins(8, 4, 8, 4)
        self._items_layout.setSpacing(2)
        self._layout.addLayout(self._items_layout)

        add_btn = QPushButton("+ Add Task")
        add_btn.setObjectName("textboxChecklistAddBtn")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(lambda: self._add_item())
        self._layout.addWidget(add_btn)

        for item_data in items or []:
            self._add_item(
                text=item_data.get("text", ""),
                checked=item_data.get("checked", False),
            )

    def _add_item(self, text: str = "", checked: bool = False):
        item = TextboxChecklistItem(text=text, checked=checked)
        item.changed.connect(self.content_changed.emit)
        item.delete_requested.connect(lambda i=item: self._remove_item(i))
        self._items_layout.addWidget(item)
        self.content_changed.emit()

    def _remove_item(self, item):
        self._items_layout.removeWidget(item)
        item.deleteLater()
        self.content_changed.emit()

    def get_content(self) -> list:
        result = []
        for i in range(self._items_layout.count()):
            w = self._items_layout.itemAt(i).widget()
            if w and isinstance(w, TextboxChecklistItem):
                result.append(w.get_data())
        return result

    def set_content(self, items: list):
        while self._items_layout.count():
            w = self._items_layout.itemAt(0).widget()
            if w:
                self._items_layout.removeWidget(w)
                w.deleteLater()
        for item_data in items:
            self._add_item(
                text=item_data.get("text", ""),
                checked=item_data.get("checked", False),
            )


# ── Table Block ─────────────────────────────────────────────────────


class TextboxTableBlock(QWidget):
    """An inline table block."""

    content_changed = pyqtSignal()
    delete_requested = pyqtSignal()

    def __init__(self, data: dict | None = None, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 4, 8, 4)
        self._layout.setSpacing(4)

        btn_row = QHBoxLayout()
        for label, handler in [
            ("+ Row", self._add_row),
            ("- Row", self._remove_row),
            ("+ Col", self._add_col),
            ("- Col", self._remove_col),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("textboxTableBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(handler)
            btn_row.addWidget(btn)
        del_btn = QPushButton("✕ Remove")
        del_btn.setObjectName("textboxTableBtn")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(self.delete_requested.emit)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        self._layout.addLayout(btn_row)

        self._table = QTableWidget(2, 3)
        self._table.setObjectName("textboxTableGrid")
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setFixedHeight(28)
        self._table.verticalHeader().setDefaultSectionSize(32)
        self._table.cellChanged.connect(lambda: self.content_changed.emit())
        self._layout.addWidget(self._table)

        if data:
            self._load_data(data)
        else:
            self._table.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])

    def _add_row(self):
        self._table.insertRow(self._table.rowCount())
        self.content_changed.emit()

    def _remove_row(self):
        if self._table.rowCount() > 1:
            self._table.removeRow(self._table.rowCount() - 1)
            self.content_changed.emit()

    def _add_col(self):
        col = self._table.columnCount()
        self._table.setColumnCount(col + 1)
        self._table.setHorizontalHeaderItem(col, QTableWidgetItem(f"Column {col + 1}"))
        self.content_changed.emit()

    def _remove_col(self):
        if self._table.columnCount() > 1:
            self._table.removeColumn(self._table.columnCount() - 1)
            self.content_changed.emit()

    def _load_data(self, data: dict):
        headers = data.get("headers", ["Column 1", "Column 2", "Column 3"])
        rows = data.get("data", [["", "", ""], ["", "", ""]])
        self._table.blockSignals(True)
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self._table.setItem(r, c, QTableWidgetItem(val))
        self._table.blockSignals(False)

    def get_content(self) -> dict:
        cols = self._table.columnCount()
        headers = []
        for c in range(cols):
            h = self._table.horizontalHeaderItem(c)
            headers.append(h.text() if h else "")
        data = []
        for r in range(self._table.rowCount()):
            row = []
            for c in range(cols):
                item = self._table.item(r, c)
                row.append(item.text() if item else "")
            data.append(row)
        return {"headers": headers, "data": data}

    def set_content(self, data: dict):
        self._load_data(data)


# ── Image Block ─────────────────────────────────────────────────────


class TextboxImageBlock(QWidget):
    """An image block that displays an image from file or URL."""

    content_changed = pyqtSignal()
    delete_requested = pyqtSignal()

    def __init__(self, data: dict | None = None, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 4, 8, 4)
        self._layout.setSpacing(4)

        btn_row = QHBoxLayout()
        file_btn = QPushButton("📁 From File")
        file_btn.setObjectName("textboxTableBtn")
        file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        file_btn.clicked.connect(self._pick_file)
        btn_row.addWidget(file_btn)

        url_btn = QPushButton("🔗 From URL")
        url_btn.setObjectName("textboxTableBtn")
        url_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        url_btn.clicked.connect(self._pick_url)
        btn_row.addWidget(url_btn)

        remove_btn = QPushButton("✕ Remove")
        remove_btn.setObjectName("textboxTableBtn")
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.clicked.connect(self.delete_requested.emit)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch()
        self._layout.addLayout(btn_row)

        self._image_label = QLabel()
        self._image_label.setObjectName("textboxImageLabel")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumHeight(60)
        self._image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self._layout.addWidget(self._image_label)

        self._source = ""
        self._path_or_url = ""

        if data:
            self.set_content(data)

    def _pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.svg)",
        )
        if path:
            self._load_image(path, "file")

    def _pick_url(self):
        from PyQt6.QtWidgets import QInputDialog

        url, ok = QInputDialog.getText(self, "Image URL", "Enter image URL:")
        if ok and url.strip():
            self._load_image(url.strip(), "url")

    def _load_image(self, path_or_url: str, source: str):
        self._source = source
        self._path_or_url = path_or_url
        if source == "file":
            pixmap = QPixmap(path_or_url)
        else:
            image = QImage()
            image.loadFromData(QDesktopServices.readUrl(QUrl(path_or_url)))
            pixmap = QPixmap.fromImage(image)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                600,
                400,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._image_label.setPixmap(scaled)
        else:
            self._image_label.setText("[Image failed to load]")
        self.content_changed.emit()

    def _remove_image(self):
        self._source = ""
        self._path_or_url = ""
        self._image_label.clear()
        self._image_label.setText("[No image]")
        self.content_changed.emit()

    def get_content(self) -> dict:
        return {"source": self._source, "path_or_url": self._path_or_url}

    def set_content(self, data: dict):
        source = data.get("source", "")
        path_or_url = data.get("path_or_url", "")
        if source and path_or_url:
            self._load_image(path_or_url, source)


# ── Main Textbox Widget ─────────────────────────────────────────────


class TextboxWidget(ResizableMixin, QWidget):
    """A floating text box with rich text, checklists, tables, and images."""

    object_delete_requested = pyqtSignal(int)

    def __init__(self, textbox_id, page_id=None, parent=None):
        super().__init__(parent)
        self.textbox_id = textbox_id
        self.page_id = page_id
        self._init_resizable_state()
        self._MIN_H = 200
        self._textbox_controller = TextboxController()
        self._blocks: list[tuple[str, QWidget]] = []
        self.setObjectName("textbox")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumHeight(self._MIN_H)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._build_header()
        self._build_content_area()
        self._build_resize_handles()
        self._install_border_filter()

    def _build_header(self):
        header = QWidget()
        header.setFixedHeight(36)
        header.setObjectName("textboxHeader")
        header.setCursor(Qt.CursorShape.OpenHandCursor)
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 4, 12, 4)
        header_layout.setSpacing(6)

        title = QLineEdit("Text Box")
        title.setObjectName("textboxTitle")
        title.setPlaceholderText("Text Box")
        title.returnPressed.connect(self._on_title_changed)
        title.editingFinished.connect(self._on_title_changed)
        self._title_edit = title
        header_layout.addWidget(title)
        header_layout.addStretch()

        insert_text_btn = QPushButton("T+ Text")
        insert_text_btn.setObjectName("textboxAddBtn")
        insert_text_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        insert_text_btn.clicked.connect(lambda: self._add_text_block())
        header_layout.addWidget(insert_text_btn)

        insert_cl_btn = QPushButton("✓ List")
        insert_cl_btn.setObjectName("textboxAddBtn")
        insert_cl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        insert_cl_btn.clicked.connect(lambda: self._add_checklist_block())
        header_layout.addWidget(insert_cl_btn)

        insert_tbl_btn = QPushButton("⊞ Table")
        insert_tbl_btn.setObjectName("textboxAddBtn")
        insert_tbl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        insert_tbl_btn.clicked.connect(lambda: self._add_table_block())
        header_layout.addWidget(insert_tbl_btn)

        insert_img_btn = QPushButton("🖼 Image")
        insert_img_btn.setObjectName("textboxAddBtn")
        insert_img_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        insert_img_btn.clicked.connect(lambda: self._add_image_block())
        header_layout.addWidget(insert_img_btn)

        fun_btn = QPushButton(" Fun")
        fun_btn.setObjectName("textboxAddBtn")
        fun_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import os

        icon_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "assets",
            "icons",
            "palette.svg",
        )
        if os.path.exists(icon_path):
            fun_btn.setIcon(QIcon(icon_path))
        fun_btn.clicked.connect(self._open_fun_imports)
        header_layout.addWidget(fun_btn)

        delete_btn = QToolButton()
        delete_btn.setObjectName("textboxDeleteBtn")
        delete_btn.setText("×")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(self._delete_textbox)
        header_layout.addWidget(delete_btn)

        self._header = header
        self._layout.addWidget(header)

    def _build_content_area(self):
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setObjectName("textboxScroll")

        container = QWidget()
        container.setObjectName("textboxContainer")
        self._blocks_layout = QVBoxLayout(container)
        self._blocks_layout.setContentsMargins(8, 8, 8, 8)
        self._blocks_layout.setSpacing(8)
        self._blocks_layout.addStretch()

        self._scroll.setWidget(container)
        self._layout.addWidget(self._scroll, 1)

    def _build_resize_handles(self):
        self._resize_handles = {}
        edges = {
            "left": (0, 0.25, 6, 0.5),
            "right": (1.0, 0.25, 6, 0.5),
            "top": (0.25, 0, 0.5, 6),
            "bottom": (0.25, 1.0, 0.5, 6),
            "top-left": (0, 0, 10, 10),
            "top-right": (1.0, 0, 10, 10),
            "bottom-left": (0, 1.0, 10, 10),
            "bottom-right": (1.0, 1.0, 10, 10),
        }
        cursors = {
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
            "top": Qt.CursorShape.SizeVerCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "top-left": Qt.CursorShape.SizeFDiagCursor,
            "top-right": Qt.CursorShape.SizeBDiagCursor,
            "bottom-left": Qt.CursorShape.SizeBDiagCursor,
            "bottom-right": Qt.CursorShape.SizeFDiagCursor,
        }
        for edge_name in edges:
            handle = QWidget(self)
            handle.setObjectName("textboxResizeHandle")
            handle.setCursor(cursors[edge_name])
            handle.installEventFilter(self)
            self._resize_handles[edge_name] = handle

    def _layout_resize_handles(self):
        w, h = self.width(), self.height()
        for edge_name, handle in self._resize_handles.items():
            rx, ry, rw, rh = {
                "left": (0, 40, 6, h - 80),
                "right": (w - 6, 40, 6, h - 80),
                "top": (40, 0, w - 80, 6),
                "bottom": (40, h - 6, w - 80, 6),
                "top-left": (0, 0, 12, 12),
                "top-right": (w - 12, 0, 12, 12),
                "bottom-left": (0, h - 12, 12, 12),
                "bottom-right": (w - 12, h - 12, 12, 12),
            }[edge_name]
            handle.setGeometry(rx, ry, rw, rh)

    def _install_border_filter(self):
        self._header.installEventFilter(self)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QMouseEvent

        if not isinstance(event, QMouseEvent):
            return super().eventFilter(obj, event)

        is_handle = obj in self._resize_handles.values()

        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                if is_handle:
                    edge = [k for k, v in self._resize_handles.items() if v is obj][0]
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
                if obj is self._header:
                    pos = obj.mapTo(self, event.position().toPoint())
                    child = self._header.childAt(pos)
                    if child is self._title_edit:
                        return False
                    if isinstance(child, QPushButton | QToolButton):
                        return False
                    self._dragging = True
                    self._drag_start = event.globalPosition().toPoint() - self.pos()
                    self._header.setCursor(Qt.CursorShape.ClosedHandCursor)
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

        if event.type() == QEvent.Type.MouseButtonRelease:
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
            if self._dragging:
                self._dragging = False
                self._drag_start = None
                self._header.setCursor(Qt.CursorShape.OpenHandCursor)
                self._save_meta()
                event.accept()
                return True

        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_resize_handles()

    def _add_text_block(self, html: str = ""):
        block = TextboxTextBlock(html=html)
        block.content_changed.connect(self._on_content_changed)
        self._insert_block("text", block)
        return block

    def _add_checklist_block(self, items: list | None = None):
        block = TextboxChecklistBlock(items=items)
        block.content_changed.connect(self._on_content_changed)
        self._insert_block("checklist", block)
        return block

    def _add_table_block(self, data: dict | None = None):
        block = TextboxTableBlock(data=data)
        block.content_changed.connect(self._on_content_changed)
        self._insert_block("table", block)
        return block

    def _add_image_block(self, data: dict | None = None):
        block = TextboxImageBlock(data=data)
        block.content_changed.connect(self._on_content_changed)
        self._insert_block("image", block)
        return block

    def _insert_block(self, block_type: str, widget: QWidget):
        idx = self._blocks_layout.count() - 1
        self._blocks_layout.insertWidget(idx, widget)
        self._blocks.append((block_type, widget))
        widget.delete_requested.connect(lambda w=widget: self._remove_block(w))
        self._on_content_changed()

    def _remove_block(self, widget):
        self._blocks_layout.removeWidget(widget)
        widget.deleteLater()
        self._blocks = [(bt, w) for bt, w in self._blocks if w is not widget]
        self._on_content_changed()

    def _on_content_changed(self):
        self._save_meta()

    def _on_title_changed(self):
        self._save_meta()

    def _open_fun_imports(self):
        from src.ui.fun_imports import FunImportsDialog

        target = None
        for block_type, widget in self._blocks:
            if block_type == "text" and isinstance(widget, TextboxTextBlock):
                if widget._editing:
                    target = widget._editor
                    break
        if target is None:
            for block_type, widget in self._blocks:
                if block_type == "text" and isinstance(widget, TextboxTextBlock):
                    widget._enter_edit_mode()
                    target = widget._editor
                    break
        if target is None:
            block = self._add_text_block()
            block._enter_edit_mode()
            target = block._editor
        dialog = FunImportsDialog(self, target_edit=target)
        dialog.exec()

    def _delete_textbox(self):
        self.object_delete_requested.emit(self.textbox_id)

    def exit_all_edit_modes(self):
        for block_type, widget in self._blocks:
            if block_type == "text" and isinstance(widget, TextboxTextBlock):
                widget.exit_edit_mode()

    def _save_meta(self):
        blocks = []
        for block_type, widget in self._blocks:
            blocks.append({"type": block_type, "content": widget.get_content()})
        self._textbox_controller.save_meta(
            page_id=self.page_id,
            textbox_id=self.textbox_id,
            x=self.x(),
            y=self.y(),
            width=self.width(),
            height=self.height(),
            title=self._title_edit.text(),
            blocks=blocks,
        )

    def _load_meta(self):
        data = self._textbox_controller.load_meta(self.page_id, self.textbox_id)
        if data:
            self._user_width = data.get("width")
            self._user_height = data.get("height")
            self._title_edit.setText(data.get("title", "Text Box"))
            x = data.get("x")
            y = data.get("y")
            if x is not None and y is not None:
                self._loaded_pos = (x, y)
                self.move(x, y)
            else:
                self._loaded_pos = None
            if self._user_width:
                self.resize(self._user_width, self._user_height or self.height())
            for block_data in data.get("blocks", []):
                block_type = block_data.get("type", "text")
                content = block_data.get("content", "")
                if block_type == "text":
                    self._add_text_block(html=content)
                elif block_type == "checklist":
                    self._add_checklist_block(items=content)
                elif block_type == "table":
                    self._add_table_block(data=content)
                elif block_type == "image":
                    self._add_image_block(data=content)
        else:
            self._loaded_pos = None

    def _min_height(self):
        return self._MIN_H

    def _on_resize_complete(self):
        self._save_meta()
