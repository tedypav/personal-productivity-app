from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QImage, QPixmap
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
    QTextBrowser,
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
    """A rich-text block with edit/render toggle."""

    content_changed = pyqtSignal()

    def __init__(self, html: str = "", parent=None):
        super().__init__(parent)
        self._html = html
        self._editing = False
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._viewer = QTextBrowser()
        self._viewer.setObjectName("textboxViewer")
        self._viewer.setOpenExternalLinks(True)
        self._viewer.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._viewer.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._viewer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self._viewer.installEventFilter(self)
        self._layout.addWidget(self._viewer)

        self._editor = QTextEdit()
        self._editor.setObjectName("textboxEditor")
        self._editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._editor.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._editor.textChanged.connect(self._on_text_changed)
        self._editor.hide()
        self._layout.addWidget(self._editor)

        self._render()

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent

        if obj is self._viewer and event.type() == QEvent.Type.MouseButtonDblClick:
            self._enter_edit_mode()
            return True
        return super().eventFilter(obj, event)

    def _enter_edit_mode(self):
        self._editing = True
        self._editor.setHtml(self._html)
        self._viewer.hide()
        self._editor.show()
        self._editor.setFocus()

    def exit_edit_mode(self):
        if self._editing:
            self._editing = False
            self._html = self._editor.toHtml()
            self._editor.hide()
            self._viewer.show()
            self._render()
            self.content_changed.emit()

    def _render(self):
        if self._html.strip():
            self._viewer.setHtml(self._html)
        else:
            self._viewer.setHtml(
                '<p style="color:#9CA3AF; font-style:italic;">'
                "Double-click to start typing...</p>"
            )
        doc_size = self._viewer.document().size()
        h = max(60, int(doc_size.height()) + 16)
        self._viewer.setMinimumHeight(h)
        self._editor.setMinimumHeight(h)

    def _on_text_changed(self):
        self._html = self._editor.toHtml()
        self._render()

    def get_content(self) -> str:
        if self._editing:
            return self._editor.toHtml()
        return self._html

    def set_content(self, html: str):
        self._html = html
        if self._editing:
            self._editor.setHtml(html)
        else:
            self._render()

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

    def __init__(self, items: list | None = None, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)

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
        remove_btn.clicked.connect(self._remove_image)
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
        self._MIN_H = 150
        self._textbox_controller = TextboxController()
        self._blocks: list[tuple[str, QWidget]] = []
        self.setObjectName("textbox")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._build_header()
        self._build_content_area()
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

    def _install_border_filter(self):
        self._header.installEventFilter(self)

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QMouseEvent

        if isinstance(event, QMouseEvent):
            pos = obj.mapTo(self, event.position().toPoint())
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    if obj is self._header:
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
        return super().eventFilter(obj, event)

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
        self._on_content_changed()

    def _on_content_changed(self):
        self._save_meta()

    def _on_title_changed(self):
        self._save_meta()

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
