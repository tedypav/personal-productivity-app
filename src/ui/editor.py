import json
from datetime import datetime, timedelta

import markdown
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout,
    QComboBox, QLabel, QCheckBox, QGridLayout, QLineEdit,
    QScrollArea, QDialog, QDialogButtonBox, QMessageBox,
    QListWidget, QFrame, QTextBrowser, QSizePolicy,
    QToolButton, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint, QMimeData
from PyQt6.QtGui import (
    QFont, QAction, QKeySequence, QTextCursor, QDrag,
    QPainter, QColor, QBrush, QPen
)

from src.repositories.block_repo import BlockRepo
from src.repositories.task_repo import TaskRepo
from src.repositories.template_repo import TemplateRepo
from src.models.content_block import ContentBlock
from src.models.task import Task


MD_EXTENSIONS = ["fenced_code", "tables", "nl2br"]


def render_markdown(text: str) -> str:
    html = markdown.markdown(text, extensions=MD_EXTENSIONS)
    return f"""<html><body style="font-family:Segoe UI, sans-serif; padding:4px 8px; line-height:1.4; font-size:13px;">{html}</body></html>"""


BLOCK_STYLE = """
QFrame#block {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
}
QFrame#block:hover {
    border-color: #6366f1;
}
"""


class MarkdownTextEdit(QTextEdit):
    focus_lost = pyqtSignal()

    def __init__(self, block_id, content="", parent=None):
        super().__init__(parent)
        self.block_id = block_id
        self.setPlainText(content)
        self.setMinimumHeight(40)
        self.setAcceptRichText(False)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_lost.emit()


class MarkdownBlock(QWidget):
    changed = pyqtSignal()

    def __init__(self, block_id, content="", parent=None):
        super().__init__(parent)
        self.block_id = block_id
        self.editing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.editor = MarkdownTextEdit(block_id, content)
        self.editor.setVisible(False)
        self.editor.focus_lost.connect(self._switch_to_preview)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        self.preview.setMinimumHeight(30)
        self.preview.mousePressEvent = lambda e: self._switch_to_edit()

        self.editor.textChanged.connect(self._on_text_changed)

        layout.addWidget(self.preview)
        layout.addWidget(self.editor)

        self._update_preview()
        self.setStyleSheet("""
            QTextBrowser { background: transparent; border: none; }
            QTextEdit { border: 1px solid #6366f1; border-radius: 4px; }
        """)

    def _switch_to_edit(self):
        if self.editing:
            return
        self.editing = True
        self.preview.setVisible(False)
        self.editor.setVisible(True)
        self.editor.setFocus()
        self.editor.moveCursor(QTextCursor.MoveOperation.End)

    def _switch_to_preview(self):
        self.editing = False
        self.editor.setVisible(False)
        self.preview.setVisible(True)
        self._update_preview()

    def _on_text_changed(self):
        self.changed.emit()
        self._update_preview()

    def _update_preview(self):
        html = render_markdown(self.editor.toPlainText())
        self.preview.setHtml(html)

    def insert_formatting(self, prefix, suffix=""):
        self._switch_to_edit()
        cursor = self.editor.textCursor()
        selected = cursor.selectedText()
        if selected:
            cursor.insertText(f"{prefix}{selected}{suffix}")
        else:
            cursor.insertText(f"{prefix}{suffix}")
            cursor.movePosition(QTextCursor.MoveOperation.Left, n=len(suffix))

    def insert_heading(self, level):
        self._switch_to_edit()
        prefix = "#" * level + " "
        self.editor.textCursor().insertText(prefix)

    def insert_link(self):
        self._switch_to_edit()
        cursor = self.editor.textCursor()
        selected = cursor.selectedText()
        if selected:
            cursor.insertText(f"[{selected}](url)")
        else:
            cursor.insertText("[link text](url)")

    def insert_bullet_list(self):
        self._switch_to_edit()
        self.editor.textCursor().insertText("- ")

    def toPlainText(self):
        return self.editor.toPlainText()


class TableCell(QTextEdit):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setPlainText(text)
        self.setAcceptRichText(False)
        self.setMinimumHeight(40)
        self.setMaximumHeight(120)


class TableWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, block_id, content="", parent=None):
        super().__init__(parent)
        self.block_id = block_id
        self.grid = QGridLayout()
        self.grid.setSpacing(2)
        self.setLayout(self.grid)
        self.rows = []
        self._parse_content(content)
        self._rebuild()

    def _parse_content(self, content):
        self.rows.clear()
        lines = content.strip().split("\n")
        for line in lines:
            if line.startswith("|") and line.endswith("|"):
                cells = [c.strip() for c in line.strip("|").split("|")]
                self.rows.append(cells)
        if not self.rows:
            self.rows = [["", ""]]

    def _rebuild(self):
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w:
                w.setParent(None)

        for r, row in enumerate(self.rows):
            for c, val in enumerate(row):
                cell = TableCell(val)
                cell.textChanged.connect(self._mark_dirty)
                self.grid.addWidget(cell, r, c)

        btn_row = len(self.rows)
        btn_add_row = QPushButton("+ Row")
        btn_del_row = QPushButton("- Row")
        btn_add_col = QPushButton("+ Col")
        btn_del_col = QPushButton("- Col")
        btn_add_row.clicked.connect(self._add_row)
        btn_del_row.clicked.connect(self._delete_last_row)
        btn_add_col.clicked.connect(self._add_col)
        btn_del_col.clicked.connect(self._delete_last_col)

        self.grid.addWidget(btn_add_row, btn_row, 0)
        self.grid.addWidget(btn_del_row, btn_row, 1)
        self.grid.addWidget(btn_add_col, btn_row, 2)
        self.grid.addWidget(btn_del_col, btn_row, 3)

    def _add_row(self):
        cols = len(self.rows[0]) if self.rows else 2
        self.rows.append([""] * cols)
        self._rebuild()
        self._mark_dirty()

    def _delete_last_row(self):
        if len(self.rows) > 1:
            self.rows.pop()
            self._rebuild()
            self._mark_dirty()

    def _add_col(self):
        for row in self.rows:
            row.append("")
        self._rebuild()
        self._mark_dirty()

    def _delete_last_col(self):
        if len(self.rows[0]) > 1:
            for row in self.rows:
                row.pop()
            self._rebuild()
            self._mark_dirty()

    def _mark_dirty(self):
        self.changed.emit()

    def to_markdown(self):
        lines = []
        for r, row in enumerate(self.rows):
            cells = []
            for c in range(len(row)):
                w = self.grid.itemAtPosition(r, c)
                text = w.widget().toPlainText() if w and w.widget() else ""
                cells.append(text)
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines)

    def save_content(self):
        BlockRepo().update(ContentBlock(id=self.block_id, content_markdown=self.to_markdown()))


class TaskWidget(QWidget):
    task_changed = pyqtSignal()

    def __init__(self, block_id, content="", parent=None):
        super().__init__(parent)
        self.block_id = block_id
        self.task_repo = TaskRepo()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._load()

    def _clear(self):
        layout = self.layout()
        for i in reversed(range(layout.count())):
            w = layout.itemAt(i).widget()
            if w:
                w.setParent(None)
            else:
                item = layout.itemAt(i)
                if item:
                    layout.removeItem(item)

    def _load(self):
        self._clear()
        layout = self.layout()

        tasks = self.task_repo.get_by_block(self.block_id)
        if not tasks:
            task = Task(content_block_id=self.block_id, text="New task")
            self.task_repo.create(task)
            tasks = [task]

        for task in tasks:
            row = QHBoxLayout()
            cb = QCheckBox()
            cb.setChecked(bool(task.is_checked))
            cb.stateChanged.connect(lambda state, t=task: self._toggle_task(t, state))
            edit = QLineEdit(task.text)
            edit.textChanged.connect(lambda text, t=task: self._update_text(t, text))

            rec_combo = QComboBox()
            rec_combo.addItems(["none", "daily", "weekly", "monthly"])
            rec_combo.setCurrentText(task.recurrence_type)

            def make_rec_handler(t):
                return lambda val: self._set_recurrence(t, val)

            rec_combo.currentTextChanged.connect(make_rec_handler(task))

            del_btn = QPushButton("X")
            del_btn.setFixedWidth(30)

            def make_del_handler(t):
                return lambda: self._delete_task(t)

            del_btn.clicked.connect(make_del_handler(task))

            row.addWidget(cb)
            row.addWidget(edit, 1)
            row.addWidget(QLabel("Recur:"))
            row.addWidget(rec_combo)
            row.addWidget(del_btn)
            layout.addLayout(row)

        add_btn = QPushButton("+ Add Task")
        add_btn.clicked.connect(self._add_task)
        layout.addWidget(add_btn)

    def _toggle_task(self, task, state):
        task.is_checked = bool(state)
        if task.is_checked and task.recurrence_type != "none":
            self._create_recurring_copy(task)
        self.task_repo.update(task)
        self.task_changed.emit()

    def _create_recurring_copy(self, task):
        days_map = {"daily": 1, "weekly": 7, "monthly": 30}
        days = days_map.get(task.recurrence_type, 7)
        old_due = task.due_date
        new_due = None
        if old_due:
            dt = datetime.strptime(old_due, "%Y-%m-%d")
            new_due = (dt + timedelta(days=days)).strftime("%Y-%m-%d")
        new_task = Task(
            content_block_id=task.content_block_id,
            text=task.text,
            recurrence_type=task.recurrence_type,
            due_date=new_due,
        )
        self.task_repo.create(new_task)
        self._load()

    def _update_text(self, task, text):
        task.text = text
        self.task_repo.update(task)

    def _set_recurrence(self, task, val):
        task.recurrence_type = val
        self.task_repo.update(task)

    def _delete_task(self, task):
        self.task_repo.delete(task.id)
        self._load()
        self.task_changed.emit()

    def _add_task(self):
        task = Task(content_block_id=self.block_id, text="New task")
        self.task_repo.create(task)
        self._load()
        self.task_changed.emit()


class DragHandle(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("⋮⋮")
        self.setFixedWidth(20)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setStyleSheet("color: #d1d5db; font-size: 12px;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class ResizeHandle(QWidget):
    def __init__(self, block_widget, parent=None):
        super().__init__(parent)
        self.block_widget = block_widget
        self.setFixedHeight(6)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.setStyleSheet("background: transparent;")
        self._dragging = False
        self._start_y = 0
        self._start_height = 0
        self.setMouseTracking(True)

    def enterEvent(self, event):
        self.setStyleSheet("background: #e0e7ff; border-radius: 2px;")

    def leaveEvent(self, event):
        if not self._dragging:
            self.setStyleSheet("background: transparent;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_y = event.globalPosition().toPoint().y()
            self._start_height = self.block_widget.height()
            self.setStyleSheet("background: #6366f1; border-radius: 2px;")

    def mouseMoveEvent(self, event):
        if self._dragging:
            delta = event.globalPosition().toPoint().y() - self._start_y
            new_h = max(60, self._start_height + delta)
            if isinstance(self.block_widget._body, MarkdownBlock):
                editor_h = max(60, new_h - 60)
                self.block_widget._body.editor.setMinimumHeight(editor_h)
                self.block_widget._body.editor.setMaximumHeight(editor_h + 20)
                self.block_widget._body.preview.setMinimumHeight(editor_h)
            elif isinstance(self.block_widget._body, TableWidget):
                for i in range(self.block_widget._body.grid.count()):
                    w = self.block_widget._body.grid.itemAt(i)
                    if w and w.widget() and isinstance(w.widget(), TableCell):
                        cell_h = max(30, (new_h - 80) // max(1, len(self.block_widget._body.rows)))
                        w.widget().setMaximumHeight(cell_h + 20)
            self.block_widget.setMinimumHeight(new_h)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self.setStyleSheet("background: #e0e7ff; border-radius: 2px;")


class ContentBlockWidget(QFrame):
    changed = pyqtSignal()
    delete_requested = pyqtSignal(object)

    def __init__(self, block: ContentBlock, index=0, parent=None):
        super().__init__(parent)
        self.block = block
        self.block_index = index
        self.setObjectName("block")
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet(BLOCK_STYLE)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.drag_handle = DragHandle()
        type_label = QLabel(f"[{self.block.block_type}]")
        type_label.setStyleSheet("color: #9ca3af; font-size: 9px; font-weight: 600;")

        del_btn = QPushButton("×")
        del_btn.setFixedSize(20, 20)
        del_btn.setStyleSheet("QPushButton { border: none; color: #9ca3af; font-size: 14px; } QPushButton:hover { color: #ef4444; }")

        header.addWidget(self.drag_handle)
        header.addWidget(type_label)
        header.addStretch()
        header.addWidget(del_btn)
        layout.addLayout(header)

        self._body = None

        if self.block.block_type == "text":
            self._body = MarkdownBlock(self.block.id, self.block.content_markdown)
            self._body.changed.connect(self._on_content_changed)
            layout.addWidget(self._body)
        elif self.block.block_type == "table":
            self._body = TableWidget(self.block.id, self.block.content_markdown)
            self._body.changed.connect(self._on_content_changed)
            layout.addWidget(self._body)
        elif self.block.block_type in ("list", "checkbox"):
            self._body = TaskWidget(self.block.id, self.block.content_markdown)
            self._body.task_changed.connect(self.changed.emit)
            layout.addWidget(self._body)

        self.resize_handle = ResizeHandle(self)
        layout.addWidget(self.resize_handle)

        del_btn.clicked.connect(self._delete)

    def _on_content_changed(self):
        self.changed.emit()

    def _delete(self):
        BlockRepo().delete(self.block.id)
        self.delete_requested.emit(self)

    def save(self):
        if self.block.block_type == "table" and self._body:
            self.block.content_markdown = self._body.to_markdown()
            BlockRepo().update(self.block)
        elif self.block.block_type == "text" and self._body:
            self.block.content_markdown = self._body.toPlainText()
            BlockRepo().update(self.block)


class DropIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)
        self.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setPen(QPen(QColor("#6366f1"), 2))
        p.drawLine(0, 2, self.width(), 2)


class PageEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page_id = None
        self.block_repo = BlockRepo()
        self.setStyleSheet("background: #ffffff;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._build_toolbar(main_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: #ffffff; }")

        self.content = QWidget()
        self.content.setStyleSheet("background: #ffffff;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 4, 12, 4)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setSpacing(4)
        scroll.setWidget(self.content)

        main_layout.addWidget(scroll, 1)

        self.drop_indicator = DropIndicator(self.content)
        self.drop_indicator.raise_()
        self.drag_source_widget = None

        self.content.setAcceptDrops(True)
        self.content.dragEnterEvent = self._drag_enter
        self.content.dragMoveEvent = self._drag_move_over
        self.content.dragLeaveEvent = self._drag_leave
        self.content.dropEvent = self._drop

    def _build_toolbar(self, parent_layout):
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet("background: #f8f9fa; border-bottom: 1px solid #e5e7eb;")
        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(8, 2, 8, 2)

        self.page_title = QLabel("Select a page")
        self.page_title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 2px 0;")
        toolbar.addWidget(self.page_title)
        toolbar.addStretch()

        btn_style = "QPushButton { padding: 3px 10px; border: 1px solid #d1d5db; border-radius: 3px; background: white; font-size: 11px; } QPushButton:hover { border-color: #6366f1; }"
        self._add_block_btn = QPushButton("+ Text")
        self._add_block_btn.setStyleSheet(btn_style)
        self._table_btn = QPushButton("+ Table")
        self._table_btn.setStyleSheet(btn_style)
        self._list_btn = QPushButton("+ List")
        self._list_btn.setStyleSheet(btn_style)
        self._template_btn = QPushButton("Template")
        self._template_btn.setStyleSheet(btn_style)

        for b in [self._add_block_btn, self._table_btn, self._list_btn, self._template_btn]:
            toolbar.addWidget(b)

        sep = QLabel("|")
        sep.setStyleSheet("color: #d1d5db; padding: 0 4px;")
        toolbar.addWidget(sep)

        tb_style = "QToolButton { font-size: 12px; border: 1px solid transparent; border-radius: 3px; padding: 2px 6px; } QToolButton:hover { border-color: #d1d5db; background: white; }"
        self._bold_btn = QToolButton()
        self._bold_btn.setText("B")
        self._bold_btn.setToolTip("Bold (Ctrl+B)")
        self._bold_btn.setStyleSheet("QToolButton { font-weight: bold; font-size: 12px; border: 1px solid transparent; border-radius: 3px; padding: 2px 6px; } QToolButton:hover { border-color: #d1d5db; background: white; }")

        self._italic_btn = QToolButton()
        self._italic_btn.setText("I")
        self._italic_btn.setToolTip("Italic (Ctrl+I)")
        self._italic_btn.setStyleSheet("QToolButton { font-style: italic; font-size: 12px; border: 1px solid transparent; border-radius: 3px; padding: 2px 6px; } QToolButton:hover { border-color: #d1d5db; background: white; }")

        self._h1_btn = QToolButton()
        self._h1_btn.setText("H1")
        self._h1_btn.setToolTip("Heading 1")
        self._h1_btn.setStyleSheet(tb_style)

        self._h2_btn = QToolButton()
        self._h2_btn.setText("H2")
        self._h2_btn.setToolTip("Heading 2")
        self._h2_btn.setStyleSheet(tb_style)

        self._code_btn = QToolButton()
        self._code_btn.setText("<>")
        self._code_btn.setToolTip("Code")
        self._code_btn.setStyleSheet(tb_style)

        self._link_btn = QToolButton()
        self._link_btn.setText("🔗")
        self._link_btn.setToolTip("Insert Link")
        self._link_btn.setStyleSheet(tb_style)

        self._bullet_btn = QToolButton()
        self._bullet_btn.setText("•")
        self._bullet_btn.setToolTip("Bullet List")
        self._bullet_btn.setStyleSheet(tb_style)

        for b in [self._bold_btn, self._italic_btn, self._h1_btn, self._h2_btn, self._code_btn, self._link_btn, self._bullet_btn]:
            toolbar.addWidget(b)

        parent_layout.addWidget(toolbar_widget)

        self._add_block_btn.clicked.connect(lambda: self._add_block("text"))
        self._table_btn.clicked.connect(lambda: self._add_block("table"))
        self._list_btn.clicked.connect(lambda: self._add_block("checkbox"))
        self._template_btn.clicked.connect(self._insert_template)
        self._bold_btn.clicked.connect(lambda: self._apply_format("bold"))
        self._italic_btn.clicked.connect(lambda: self._apply_format("italic"))
        self._h1_btn.clicked.connect(lambda: self._apply_format("h1"))
        self._h2_btn.clicked.connect(lambda: self._apply_format("h2"))
        self._code_btn.clicked.connect(lambda: self._apply_format("code"))
        self._link_btn.clicked.connect(lambda: self._apply_format("link"))
        self._bullet_btn.clicked.connect(lambda: self._apply_format("bullet"))

    def _get_active_text_block(self):
        if not hasattr(self, '_block_widgets'):
            return None
        for w in self._block_widgets:
            if hasattr(w, '_body') and isinstance(w._body, MarkdownBlock):
                if w._body.editor.hasFocus():
                    return w._body
        return None

    def _apply_format(self, fmt):
        body = self._get_active_text_block()
        if not body:
            return
        if fmt == "bold":
            body.insert_formatting("**", "**")
        elif fmt == "italic":
            body.insert_formatting("*", "*")
        elif fmt == "h1":
            body.insert_heading(1)
        elif fmt == "h2":
            body.insert_heading(2)
        elif fmt == "code":
            body.insert_formatting("`", "`")
        elif fmt == "link":
            body.insert_link()
        elif fmt == "bullet":
            body.insert_bullet_list()

    def load_page(self, page_id: int):
        self.current_page_id = page_id
        from src.repositories.page_repo import PageRepo
        page = PageRepo().get_by_id(page_id)
        self.page_title.setText(page.title if page else "Untitled")

        for w in getattr(self, '_block_widgets', []):
            w.setParent(None)
            w.deleteLater()
        self._block_widgets = []

        blocks = self.block_repo.get_by_page(page_id)
        if not blocks:
            default = ContentBlock(page_id=page_id, block_type="text", content_markdown="")
            self.block_repo.create(default)
            blocks = [default]

        for i, block in enumerate(blocks):
            w = ContentBlockWidget(block, index=i)
            w.changed.connect(self._on_block_changed)
            w.delete_requested.connect(self._on_block_deleted)
            self._setup_drag(w)
            self.content_layout.addWidget(w)
            self._block_widgets.append(w)

    def _setup_drag(self, widget):
        widget.drag_handle.mousePressEvent = lambda e: self._drag_start(widget, e)
        widget.drag_handle.mouseMoveEvent = lambda e: self._drag_move(widget, e)

    def _drag_start(self, widget, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_source_widget = widget
            drag = QDrag(widget)
            mime = QMimeData()
            mime.setText(str(id(widget)))
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.MoveAction)

    def _drag_move(self, widget, event):
        pass

    def _on_block_changed(self):
        pass

    def _on_block_deleted(self, widget):
        if widget in self._block_widgets:
            self._block_widgets.remove(widget)
            widget.setParent(None)
            widget.deleteLater()

    def _add_block(self, block_type: str):
        if not self.current_page_id:
            return
        block = ContentBlock(page_id=self.current_page_id, block_type=block_type)
        self.block_repo.create(block)
        self.load_page(self.current_page_id)

    def _reorder_blocks(self):
        for i, w in enumerate(self._block_widgets):
            w.block.sort_order = i
            BlockRepo().update(w.block)

    def _insert_template(self):
        if not self.current_page_id:
            return
        repo = TemplateRepo()
        templates = repo.get_all()
        if not templates:
            QMessageBox.information(self, "Templates", "No templates saved yet.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Insert Template")
        layout = QVBoxLayout(dialog)
        list_widget = QListWidget()
        for t in templates:
            list_widget.addItem(f"{t.name} ({t.category})")
        layout.addWidget(list_widget)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted and list_widget.currentRow() >= 0:
            template = templates[list_widget.currentRow()]
            blocks_data = json.loads(template.content_json)
            for bd in blocks_data:
                block = ContentBlock(
                    page_id=self.current_page_id,
                    block_type=bd.get("block_type", "text"),
                    content_markdown=bd.get("content_markdown", "")
                )
                self.block_repo.create(block)
            self.load_page(self.current_page_id)

    def _get_drop_index(self, pos_y):
        best_idx = len(self._block_widgets)
        best_dist = float('inf')
        for i, w in enumerate(self._block_widgets):
            wy = w.y()
            wh = w.height()
            mid = wy + wh // 2
            dist = abs(pos_y - mid)
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        # decide above or below based on which half
        if best_idx < len(self._block_widgets):
            w = self._block_widgets[best_idx]
            mid = w.y() + w.height() // 2
            if pos_y > mid:
                best_idx += 1
        return best_idx

    def _show_drop_indicator(self, pos_y):
        idx = self._get_drop_index(pos_y)
        if idx < len(self._block_widgets):
            target = self._block_widgets[idx]
            self.drop_indicator.setFixedWidth(target.width())
            self.drop_indicator.move(target.x(), target.y() - 2)
        elif self._block_widgets:
            target = self._block_widgets[-1]
            self.drop_indicator.setFixedWidth(target.width())
            self.drop_indicator.move(target.x(), target.y() + target.height() - 2)
        else:
            self.drop_indicator.setFixedWidth(self.content.width())
            self.drop_indicator.move(0, 0)
        self.drop_indicator.show()

    def _drag_enter(self, event):
        if event.mimeData().hasText() and self.drag_source_widget:
            event.acceptProposedAction()
            self._show_drop_indicator(event.position().toPoint().y())

    def _drag_move_over(self, event):
        if event.mimeData().hasText() and self.drag_source_widget:
            event.acceptProposedAction()
            self._show_drop_indicator(event.position().toPoint().y())

    def _drag_leave(self, event):
        self.drop_indicator.hide()

    def _drop(self, event):
        self.drop_indicator.hide()
        if not self.drag_source_widget:
            return
        source = self.drag_source_widget
        pos = event.position().toPoint()
        target_idx = self._get_drop_index(pos.y())
        source_idx = self._block_widgets.index(source)

        if source_idx == target_idx or (source_idx + 1 == target_idx):
            self.drag_source_widget = None
            return

        if source_idx < target_idx:
            target_idx -= 1

        self.content_layout.removeWidget(source)
        self._block_widgets.remove(source)
        self._block_widgets.insert(target_idx, source)
        self.content_layout.insertWidget(target_idx, source)
        self._reorder_blocks()
        self.drag_source_widget = None

    def save_current(self):
        for w in getattr(self, '_block_widgets', []):
            if hasattr(w, 'save'):
                w.save()
