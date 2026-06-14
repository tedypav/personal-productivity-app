import json

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.controllers.table_controller import TableController
from src.models.page_object import PageObject
from src.repositories.page_object_repo import PageObjectRepo
from src.ui.objects.resizable_mixin import ResizableMixin

__all__ = ["TableWidget"]


class TabTableWidget(QTableWidget):
    """QTableWidget with custom Tab handling for auto-adding rows."""

    def __init__(self, rows, cols, parent=None):
        super().__init__(rows, cols, parent)
        self._custom_tab_handler = None

    def setCustomTabHandler(self, handler):
        self._custom_tab_handler = handler

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            if self._custom_tab_handler:
                self._custom_tab_handler(event)
                event.accept()
                return
        super().keyPressEvent(event)


class TableWidget(ResizableMixin, QWidget):
    """A floating table card with editable cells."""

    object_changed = pyqtSignal(int, str)
    object_delete_requested = pyqtSignal(int)

    def __init__(self, table_id, page_id=None, parent=None):
        super().__init__(parent)
        self.table_id = table_id
        self.page_id = page_id
        self._init_resizable_state()
        self._MIN_H = 100
        self._table_controller = TableController()
        self.setObjectName("tableCard")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._build_header()
        self._build_table()
        self._install_border_filter()

    def _build_header(self):
        header = QWidget()
        header.setFixedHeight(36)
        header.setObjectName("tableHeader")
        header.setCursor(Qt.CursorShape.OpenHandCursor)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 4, 12, 4)
        header_layout.setSpacing(6)

        title = QLineEdit("Table")
        title.setObjectName("tableTitle")
        title.setPlaceholderText("Table")
        title.returnPressed.connect(self._on_title_changed)
        title.editingFinished.connect(self._on_title_changed)
        self._title_edit = title
        header_layout.addWidget(title)
        header_layout.addStretch()

        add_row_btn = QPushButton("+ Row")
        add_row_btn.setObjectName("tableAddBtn")
        add_row_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_row_btn.clicked.connect(self._add_row)
        header_layout.addWidget(add_row_btn)

        add_col_btn = QPushButton("+ Col")
        add_col_btn.setObjectName("tableAddBtn")
        add_col_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_col_btn.clicked.connect(self._add_column)
        header_layout.addWidget(add_col_btn)

        remove_row_btn = QPushButton("- Row")
        remove_row_btn.setObjectName("tableRemoveBtn")
        remove_row_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_row_btn.clicked.connect(self._remove_row)
        header_layout.addWidget(remove_row_btn)

        remove_col_btn = QPushButton("- Col")
        remove_col_btn.setObjectName("tableRemoveBtn")
        remove_col_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_col_btn.clicked.connect(self._remove_column)
        header_layout.addWidget(remove_col_btn)

        self._row_num_btn = QPushButton("#")
        self._row_num_btn.setObjectName("tableRowNumBtn")
        self._row_num_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._row_num_btn.setCheckable(True)
        self._row_num_btn.clicked.connect(self._toggle_row_numbers)
        header_layout.addWidget(self._row_num_btn)

        delete_btn = QToolButton()
        delete_btn.setObjectName("tableDeleteBtn")
        delete_btn.setText("×")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(self._delete_table)
        header_layout.addWidget(delete_btn)

        self._header = header
        self._layout.addWidget(header)

    def _build_table(self):
        from PyQt6.QtWidgets import QSizePolicy

        self._table = TabTableWidget(2, 3)
        self._table.setCustomTabHandler(self._handle_tab)
        self._table.setObjectName("tableGrid")
        self._table.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionMode(QTableWidget.SelectionMode.ContiguousSelection)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setFixedHeight(28)
        self._table.verticalHeader().setDefaultSectionSize(32)
        self._table.verticalHeader().setMinimumSectionSize(24)
        self._table.horizontalHeader().sectionDoubleClicked.connect(self._rename_column)
        self._table.setMinimumHeight(0)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        for c in range(self._table.columnCount()):
            self._table.horizontalHeader().setSectionResizeMode(
                c, self._table.horizontalHeader().ResizeMode.Stretch
            )
        self._table.cellChanged.connect(self._on_cell_changed)
        self._layout.addWidget(self._table)

    def sizeHint(self):
        header_h = 36
        table_header_h = 28
        rows = self._table.rowCount()
        row_h = 32
        total_h = header_h + table_header_h + (rows * row_h)
        return QSize(self.width(), total_h)

    def _scale_rows_to_fit(self):
        table_header_h = self._table.horizontalHeader().height()
        rows = self._table.rowCount()
        if rows == 0:
            return
        available_h = self.height() - self._header.height() - table_header_h
        available_h = max(0, available_h)
        row_h = max(24, available_h // rows)
        for r in range(rows):
            self._table.verticalHeader().resizeSection(r, row_h)

    def mouseMoveEvent(self, event):
        was_resizing = self._resizing
        super().mouseMoveEvent(event)
        if was_resizing:
            self._scale_rows_to_fit()

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
        self._table.installEventFilter(self)
        self._table.viewport().installEventFilter(self)
        self._header.installEventFilter(self)

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent, QMouseEvent

        if isinstance(event, QKeyEvent):
            is_viewport = obj is self._table.viewport()
            is_viewport_child = self._table.viewport().isAncestorOf(obj)
            is_table = obj is self._table
            if not is_viewport and not is_viewport_child and not is_table:
                return super().eventFilter(obj, event)
            if event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_Tab:
                    self._handle_tab(event)
                    event.accept()
                    return True
                if event.key() == Qt.Key.Key_Backtab:
                    self._handle_tab(event, reverse=True)
                    event.accept()
                    return True

        if isinstance(event, QMouseEvent):
            pos = obj.mapTo(self, event.position().toPoint())
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    if pos.y() <= self._header.height():
                        child = self._header.childAt(pos)
                        if child is self._title_edit:
                            return False
                        self.setFocus()
                        self._dragging = True
                        self._drag_start = event.globalPosition().toPoint() - self.pos()
                        self._header.setCursor(Qt.CursorShape.ClosedHandCursor)
                        event.accept()
                        return True
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
                        new_x = max(
                            0,
                            min(
                                new_pos.x(),
                                parent.width() - self.width(),
                            ),
                        )
                        new_y = max(
                            0,
                            min(
                                new_pos.y(),
                                parent.height() - self.height(),
                            ),
                        )
                        self.move(new_x, new_y)
                    event.accept()
                    return True
                if self._resizing and self._resize_start is not None:
                    curr = event.globalPosition().toPoint()
                    dx = curr.x() - self._resize_start.x()
                    dy = curr.y() - self._resize_start.y()
                    ox, oy, ow, oh = self._resize_origin
                    edge = self._resize_edge
                    new_x, new_y, new_w, new_h = (
                        ox,
                        oy,
                        ow,
                        oh,
                    )
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
                        new_x = max(
                            0,
                            min(new_x, parent.width() - new_w),
                        )
                        new_y = max(
                            0,
                            min(new_y, parent.height() - new_h),
                        )
                    self._user_width = new_w
                    self.setMinimumWidth(0)
                    self.setMaximumWidth(16777215)
                    self.setGeometry(new_x, new_y, new_w, new_h)
                    self._scale_rows_to_fit()
                    event.accept()
                    return True
                edge = self._detect_edge(pos)
                if edge and not self._resizing and not self._dragging:
                    self.setCursor(self._edge_cursor(edge))
                elif not edge and not self._resizing and not self._dragging:
                    self.setCursor(Qt.CursorShape.ArrowCursor)

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
                    self._scale_rows_to_fit()
                    self._save_meta()

        self._table.setCurrentCell(row, col)

    def _save_meta(self):
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
                "height": self.height(),
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
            obj = PageObject(
                page_id=self.page_id,
                object_type="table_meta",
                content=content,
                sort_order=self.table_id * 100 + 50,
            )
            repo.create(obj)

    def _load_meta(self):
        meta = PageObjectRepo().get_table_meta(self.page_id, self.table_id)
        if meta:
            try:
                data = json.loads(meta.content)
            except (json.JSONDecodeError, ValueError):
                self._loaded_pos = None
                return
            self._user_width = data.get("width")
            self._user_height = data.get("height")
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
            if self._user_width:
                self.resize(self._user_width, self._user_height or self.height())
        else:
            self._loaded_pos = None

    def _min_height(self):
        return self._MIN_H
