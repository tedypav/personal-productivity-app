import json
from datetime import datetime, timedelta

import markdown
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout,
    QComboBox, QLabel, QCheckBox, QGridLayout, QLineEdit,
    QScrollArea, QDialog, QDialogButtonBox, QMessageBox,
    QListWidget, QFrame, QTextBrowser, QSplitter, QSizePolicy,
    QToolButton, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QAction, QKeySequence, QTextCursor

from src.repositories.block_repo import BlockRepo
from src.repositories.task_repo import TaskRepo
from src.repositories.template_repo import TemplateRepo
from src.models.content_block import ContentBlock
from src.models.task import Task


MD_EXTENSIONS = ["fenced_code", "tables", "nl2br"]


def render_markdown(text: str) -> str:
    html = markdown.markdown(text, extensions=MD_EXTENSIONS)
    return f"""<html><body style="font-family:Segoe UI, sans-serif; padding:8px;">{html}</body></html>"""


class MarkdownTextEdit(QTextEdit):
    def __init__(self, block_id, content="", parent=None):
        super().__init__(parent)
        self.block_id = block_id
        self.setPlainText(content)
        self.setMinimumHeight(60)
        self.setAcceptRichText(False)


class MarkdownBlock(QWidget):
    changed = pyqtSignal()

    def __init__(self, block_id, content="", parent=None):
        super().__init__(parent)
        self.block_id = block_id
        self.preview_mode = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.editor = MarkdownTextEdit(block_id, content)
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        self.preview.setMinimumHeight(60)
        self.preview.setVisible(False)

        self.editor.textChanged.connect(self._on_text_changed)

        layout.addWidget(self.editor)
        layout.addWidget(self.preview)

    def _on_text_changed(self):
        self.changed.emit()
        if self.preview_mode:
            self._update_preview()

    def _update_preview(self):
        self.preview.setHtml(render_markdown(self.editor.toPlainText()))

    def toggle_preview(self):
        self.preview_mode = not self.preview_mode
        self.editor.setVisible(not self.preview_mode)
        self.preview.setVisible(self.preview_mode)
        if self.preview_mode:
            self._update_preview()

    def insert_formatting(self, prefix, suffix=""):
        cursor = self.editor.textCursor()
        selected = cursor.selectedText()
        if selected:
            cursor.insertText(f"{prefix}{selected}{suffix}")
        else:
            cursor.insertText(f"{prefix}{suffix}")
            # move cursor between prefix/suffix
            cursor.movePosition(QTextCursor.MoveOperation.Left, n=len(suffix))

    def insert_heading(self, level):
        prefix = "#" * level + " "
        cursor = self.editor.textCursor()
        cursor.insertText(prefix)

    def insert_link(self):
        cursor = self.editor.textCursor()
        selected = cursor.selectedText()
        if selected:
            cursor.insertText(f"[{selected}](url)")
        else:
            cursor.insertText("[link text](url)")

    def insert_bullet_list(self):
        cursor = self.editor.textCursor()
        cursor.insertText("- ")

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
        for row in self.rows:
            cells = []
            for c, _ in enumerate(row):
                w = self.grid.itemAtPosition(len(lines), c)
                text = w.widget().toPlainText() if w and w.widget() else ""
                cells.append(text)
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines)


class TaskWidget(QWidget):
    task_changed = pyqtSignal()

    def __init__(self, block_id, content="", parent=None):
        super().__init__(parent)
        self.block_id = block_id
        self.task_repo = TaskRepo()
        self.block_repo = BlockRepo()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._load()

    def _load(self):
        layout = self.layout()
        for i in reversed(range(layout.count())):
            w = layout.itemAt(i).widget()
            if w:
                w.setParent(None)

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
            rec_combo.currentTextChanged.connect(lambda val, t=task: self._set_recurrence(t, val))

            del_btn = QPushButton("X")
            del_btn.setFixedWidth(30)
            del_btn.clicked.connect(lambda checked, t=task: self._delete_task(t))

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


class ContentBlockWidget(QFrame):
    changed = pyqtSignal()
    delete_requested = pyqtSignal(object)

    def __init__(self, block: ContentBlock, parent=None):
        super().__init__(parent)
        self.block = block
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)

        header = QHBoxLayout()
        type_label = QLabel(f"[{self.block.block_type}]")
        type_label.setStyleSheet("font-weight: bold; color: #888; font-size: 11px;")

        preview_btn = QPushButton("Preview")
        preview_btn.setFixedWidth(70)
        preview_btn.setVisible(self.block.block_type == "text")

        del_btn = QPushButton("X")
        del_btn.setFixedWidth(30)

        header.addWidget(type_label)
        header.addStretch()
        header.addWidget(preview_btn)
        header.addWidget(del_btn)
        layout.addLayout(header)

        self._body = None

        if self.block.block_type == "text":
            self._body = MarkdownBlock(self.block.id, self.block.content_markdown)
            self._body.changed.connect(self._on_content_changed)
            preview_btn.clicked.connect(self._body.toggle_preview)
            layout.addWidget(self._body)
        elif self.block.block_type == "table":
            self._body = TableWidget(self.block.id, self.block.content_markdown)
            self._body.changed.connect(self._on_content_changed)
            layout.addWidget(self._body)
        elif self.block.block_type in ("list", "checkbox"):
            self._body = TaskWidget(self.block.id, self.block.content_markdown)
            self._body.task_changed.connect(self.changed.emit)
            layout.addWidget(self._body)

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


class PageEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page_id = None
        self.block_repo = BlockRepo()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._build_toolbar(main_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setSpacing(4)
        scroll.setWidget(self.content)

        main_layout.addWidget(scroll, 1)

    def _build_toolbar(self, parent_layout):
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(4, 4, 4, 4)

        self.page_title = QLabel("Select a page")
        self.page_title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px;")
        toolbar.addWidget(self.page_title)
        toolbar.addStretch()

        self._add_block_btn = QPushButton("+ Text")
        self._table_btn = QPushButton("+ Table")
        self._list_btn = QPushButton("+ List")
        self._template_btn = QPushButton("Insert Template")

        self._bold_btn = QToolButton()
        self._bold_btn.setText("B")
        self._bold_btn.setToolTip("Bold (Ctrl+B)")
        self._bold_btn.setStyleSheet("font-weight: bold; font-size: 14px;")
        self._bold_btn.setFixedSize(32, 32)
        self._bold_btn.setCheckable(True)

        self._italic_btn = QToolButton()
        self._italic_btn.setText("I")
        self._italic_btn.setToolTip("Italic (Ctrl+I)")
        self._italic_btn.setStyleSheet("font-style: italic; font-size: 14px;")
        self._italic_btn.setFixedSize(32, 32)

        self._h1_btn = QToolButton()
        self._h1_btn.setText("H1")
        self._h1_btn.setToolTip("Heading 1")
        self._h1_btn.setFixedSize(36, 32)

        self._h2_btn = QToolButton()
        self._h2_btn.setText("H2")
        self._h2_btn.setToolTip("Heading 2")
        self._h2_btn.setFixedSize(36, 32)

        self._code_btn = QToolButton()
        self._code_btn.setText("<>")
        self._code_btn.setToolTip("Code")
        self._code_btn.setFixedSize(32, 32)

        self._link_btn = QToolButton()
        self._link_btn.setText("🔗")
        self._link_btn.setToolTip("Insert Link")
        self._link_btn.setFixedSize(32, 32)

        self._bullet_btn = QToolButton()
        self._bullet_btn.setText("•")
        self._bullet_btn.setToolTip("Bullet List")
        self._bullet_btn.setFixedSize(32, 32)

        for b in [self._add_block_btn, self._table_btn, self._list_btn, self._template_btn]:
            toolbar.addWidget(b)

        toolbar.addSpacing(16)

        sep = QLabel("|")
        sep.setStyleSheet("color: #ccc;")
        toolbar.addWidget(sep)

        for b in [self._bold_btn, self._italic_btn, self._h1_btn, self._h2_btn, self._code_btn, self._link_btn, self._bullet_btn]:
            toolbar.addWidget(b)

        parent_layout.addLayout(toolbar)

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
            default = ContentBlock(page_id=page_id, block_type="text", content_markdown="Start writing...")
            self.block_repo.create(default)
            blocks = [default]

        for block in blocks:
            w = ContentBlockWidget(block)
            w.changed.connect(self._on_block_changed)
            w.delete_requested.connect(self._on_block_deleted)
            self.content_layout.addWidget(w)
            self._block_widgets.append(w)

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

    def save_current(self):
        for w in getattr(self, '_block_widgets', []):
            if hasattr(w, 'save'):
                w.save()
