import json
import traceback
from datetime import datetime, timedelta

import markdown
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout,
    QComboBox, QLabel, QCheckBox, QGridLayout, QLineEdit,
    QScrollArea, QDialog, QDialogButtonBox, QMessageBox,
    QListWidget, QFrame, QTextBrowser, QSizePolicy,
    QToolButton, QApplication, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint, QEvent
from PyQt6.QtGui import (
    QFont, QAction, QKeySequence, QTextCursor, QTextCharFormat,
    QPainter, QColor
)

from src.repositories.block_repo import BlockRepo
from src.repositories.task_repo import TaskRepo
from src.repositories.template_repo import TemplateRepo
from src.models.content_block import ContentBlock
from src.models.task import Task
from src.undo_manager import undo_manager


MD_EXTENSIONS = ["fenced_code", "tables", "nl2br"]


def render_markdown(text: str, font_size: int = 13) -> str:
    html = markdown.markdown(text, extensions=MD_EXTENSIONS)
    return f"""<html><body style="font-family:Segoe UI, sans-serif; padding:4px 8px; line-height:1.4; font-size:{font_size}px;">{html}</body></html>"""


BLOCK_STYLE = """
QFrame#block {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
}
QFrame#block:hover {
    border-color: #6366f1;
}
QFrame#block[selected="true"] {
    border: 2px solid #6366f1;
    background: #f8f8ff;
}
"""


class MarkdownTextEdit(QTextEdit):
    focus_lost = pyqtSignal()
    focused = pyqtSignal()

    def __init__(self, block_id, content="", parent=None):
        super().__init__(parent)
        self.block_id = block_id
        self.setMinimumHeight(30)
        self.setAcceptRichText(True)
        self._set_content(content)

    def _set_content(self, content):
        content = content or ""
        stripped = content.strip()
        if stripped.startswith("<") and ">" in stripped:
            self.setHtml(content)
        else:
            import markdown
            html = markdown.markdown(content, extensions=["fenced_code", "tables", "nl2br"])
            wrapped = f'<html><body style="font-family:Segoe UI, sans-serif; font-size:13px;">{html}</body></html>'
            self.setHtml(wrapped)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focused.emit()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_lost.emit()


class MarkdownBlock(QWidget):
    changed = pyqtSignal()

    def __init__(self, block_id, content="", parent=None, content_font_size=None):
        super().__init__(parent)
        self.block_id = block_id
        self.editing = False
        self.content_font_size = content_font_size or 13

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.editor = MarkdownTextEdit(block_id, content)
        self.editor.setVisible(False)
        self.editor.focus_lost.connect(self._switch_to_preview)

        if self.content_font_size:
            font = self.editor.document().defaultFont()
            font.setPointSize(self.content_font_size)
            self.editor.document().setDefaultFont(font)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        self.preview.setMinimumHeight(30)
        self.preview.mousePressEvent = lambda e: self._switch_to_edit()

        self.editor.textChanged.connect(self._on_text_changed)
        self._pending_font_size = None
        self.editor.focused.connect(lambda: QTimer.singleShot(0, self._apply_pending_font))

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

    def _apply_pending_font(self):
        if self._pending_font_size:
            fmt = QTextCharFormat()
            fmt.setFontPointSize(self._pending_font_size)
            self.editor.setCurrentCharFormat(fmt)
            self._pending_font_size = None

    def set_content_font_size(self, size):
        self.content_font_size = size
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            fmt.setFontPointSize(size)
            cursor.mergeCharFormat(fmt)
        else:
            fmt = QTextCharFormat()
            fmt.setFontPointSize(size)
            self.editor.setCurrentCharFormat(fmt)
            self._pending_font_size = size
        self._update_preview()

    def _on_text_changed(self):
        self.changed.emit()
        self._update_preview()

    def _update_preview(self):
        html = self.editor.toHtml()
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
    def __init__(self, text="", row=0, col=0, table_widget=None, parent=None):
        super().__init__(parent)
        self.setPlainText(text)
        self.setAcceptRichText(False)
        self.setMinimumHeight(40)
        self.setMaximumHeight(120)
        self._table_row = row
        self._table_col = col
        self._table = table_widget

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Tab:
            self._table._focus_next_cell(self._table_row, self._table_col)
            event.accept()
        elif event.key() == Qt.Key.Key_Backtab:
            self._table._focus_prev_cell(self._table_row, self._table_col)
            event.accept()
        else:
            super().keyPressEvent(event)


class TableWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, block_id, content="", parent=None):
        super().__init__(parent)
        self.block_id = block_id
        self.grid = QGridLayout()
        self.grid.setSpacing(2)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self._build_toolbar(main_layout)
        main_layout.addLayout(self.grid)
        self.rows = []
        self._parse_content(content)
        self._rebuild()

    def _build_toolbar(self, parent):
        bar = QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)
        btn_style = "QPushButton { font-size: 11px; padding: 2px 8px; border: 1px solid #d1d5db; border-radius: 3px; background: #f9fafb; } QPushButton:hover { border-color: #6366f1; }"
        btn_add_row = QPushButton("+ Row")
        btn_add_row.setStyleSheet(btn_style)
        btn_del_row = QPushButton("- Row")
        btn_del_row.setStyleSheet(btn_style)
        btn_add_col = QPushButton("+ Col")
        btn_add_col.setStyleSheet(btn_style)
        btn_del_col = QPushButton("- Col")
        btn_del_col.setStyleSheet(btn_style)
        btn_add_row.clicked.connect(self._add_row)
        btn_del_row.clicked.connect(self._delete_last_row)
        btn_add_col.clicked.connect(self._add_col)
        btn_del_col.clicked.connect(self._delete_last_col)
        bar.addWidget(btn_add_row)
        bar.addWidget(btn_del_row)
        bar.addWidget(btn_add_col)
        bar.addWidget(btn_del_col)
        bar.addStretch()
        parent.addLayout(bar)

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
                cell = TableCell(val, row=r, col=c, table_widget=self)
                cell.textChanged.connect(self._mark_dirty)
                self.grid.addWidget(cell, r, c)

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

    def _focus_next_cell(self, r, c):
        if r == len(self.rows) - 1 and c == len(self.rows[0]) - 1:
            self._add_row()
            r = len(self.rows) - 1
            c = 0
        elif c < len(self.rows[0]) - 1:
            c += 1
        else:
            r += 1
            c = 0
        w = self.grid.itemAtPosition(r, c)
        if w and w.widget():
            w.widget().setFocus()

    def _focus_prev_cell(self, r, c):
        if c > 0:
            c -= 1
        elif r > 0:
            r -= 1
            c = len(self.rows[0]) - 1
        else:
            return
        w = self.grid.itemAtPosition(r, c)
        if w and w.widget():
            w.widget().setFocus()

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
        from src.undo_manager import _task_dict
        undo_manager.push({
            "type": "task",
            "task": _task_dict(task),
        })
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
    CORNER_WIDTH = 24

    def __init__(self, block_widget, parent=None):
        super().__init__(parent)
        self.block_widget = block_widget
        self.setFixedHeight(14)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.setStyleSheet("background: #f0f0ff; border-top: 1px solid #e5e7eb;")
        self._dragging = False
        self._start_y = 0
        self._start_x = 0
        self._start_height = 0
        self._start_width = 0
        self._in_corner = False
        self.setMouseTracking(True)

    def _is_in_corner(self, pos_x):
        return pos_x >= self.width() - self.CORNER_WIDTH

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        h = self.height()
        w = self.width()
        corner_x = w - self.CORNER_WIDTH
        p.setPen(QColor("#d1d5db"))
        for i in range(3):
            y = h - 4 - i * 4
            p.drawLine(corner_x + 4 + i * 4, y, corner_x + 4 + i * 4 + 4, y)

    def enterEvent(self, event):
        self.setStyleSheet("background: #e0e7ff; border-top: 1px solid #6366f1;")

    def leaveEvent(self, event):
        if not self._dragging:
            self.setStyleSheet("background: #f0f0ff; border-top: 1px solid #e5e7eb;")
            self._in_corner = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_y = event.globalPosition().toPoint().y()
            self._start_x = event.globalPosition().toPoint().x()
            self._start_height = self.block_widget.height()
            self._start_width = self.block_widget.width()
            self._in_corner = self._is_in_corner(event.position().toPoint().x())
            self.setStyleSheet("background: #6366f1; border-radius: 2px;")

    def mouseMoveEvent(self, event):
        if self._dragging:
            delta_y = event.globalPosition().toPoint().y() - self._start_y
            delta_x = event.globalPosition().toPoint().x() - self._start_x
            new_h = max(60, self._start_height + delta_y)
            new_w = max(200, self._start_width + delta_x)
            parent = self.block_widget.parent()
            if parent:
                new_w = min(new_w, parent.width() - self.block_widget.x())
            if self._in_corner:
                self.block_widget.setFixedWidth(new_w)
                self.block_widget.setFixedHeight(new_h)
            else:
                self.block_widget.setMinimumHeight(new_h)
                self.block_widget.setFixedWidth(new_w)
            if isinstance(self.block_widget._body, MarkdownBlock):
                editor_h = max(30, new_h - 60)
                self.block_widget._body.editor.setMinimumHeight(editor_h)
                self.block_widget._body.preview.setMinimumHeight(editor_h)
            elif isinstance(self.block_widget._body, TableWidget):
                for i in range(self.block_widget._body.grid.count()):
                    it = self.block_widget._body.grid.itemAt(i)
                    if it and it.widget() and isinstance(it.widget(), TableCell):
                        cell_h = max(30, (new_h - 80) // max(1, len(self.block_widget._body.rows)))
                        it.widget().setMaximumHeight(cell_h + 20)
        else:
            in_corner = self._is_in_corner(event.position().toPoint().x())
            if in_corner != self._in_corner:
                self._in_corner = in_corner
                self.setCursor(Qt.CursorShape.SizeFDiagCursor if in_corner else Qt.CursorShape.SizeVerCursor)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self.setStyleSheet("background: #e0e7ff; border-radius: 2px;")
        if hasattr(self.block_widget, 'save'):
            self.block_widget.save()


class ResizeHandleHeader(QWidget):
    def __init__(self, header_container, parent=None):
        super().__init__(parent)
        self._header_container = header_container
        self.setFixedHeight(8)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.setStyleSheet("background: transparent;")
        self._dragging = False
        self._start_y = 0
        self._start_h = 0

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        w = self.width()
        p.setPen(QColor("#d1d5db"))
        cx = w // 2
        for i in range(3):
            y = 2 + i * 2
            p.drawLine(cx - 8 + i * 4, y, cx + 4 + i * 4, y)

    def enterEvent(self, event):
        self.setStyleSheet("background: #e0e7ff; border-top: 1px solid #6366f1; border-bottom: 1px solid #6366f1;")

    def leaveEvent(self, event):
        if not self._dragging:
            self.setStyleSheet("background: transparent;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_y = event.globalPosition().toPoint().y()
            self._start_h = self._header_container.height()
            self.setStyleSheet("background: #6366f1;")

    def mouseMoveEvent(self, event):
        if self._dragging:
            delta = event.globalPosition().toPoint().y() - self._start_y
            new_h = max(36, self._start_h + delta)
            self._header_container.setFixedHeight(new_h)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self.setStyleSheet("background: #e0e7ff;")
        block_w = self._header_container.parent()
        while block_w and not isinstance(block_w, ContentBlockWidget):
            block_w = block_w.parent()
        if block_w:
            block_w.save()


class ContentBlockWidget(QFrame):
    changed = pyqtSignal()
    delete_requested = pyqtSignal(object)
    clicked = pyqtSignal(object, bool)  # (self, add_to_selection)
    header_focused = pyqtSignal(object)  # self
    content_focused = pyqtSignal(object)  # self
    saved = pyqtSignal()

    def __init__(self, block: ContentBlock, index=0, parent=None):
        super().__init__(parent)
        self.block = block
        self.block_index = index
        self._selected = False
        self.setObjectName("block")
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet(BLOCK_STYLE)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setMouseTracking(True)
        self._right_resizing = False
        self._right_resize_start_x = 0
        self._right_resize_start_w = 0
        self._align_target_edit = None
        self._align_target_kind = None

        self._build_ui()

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.position().toPoint().x() >= self.width() - 8:
                self._right_resizing = True
                self._right_resize_start_x = event.globalPosition().toPoint().x()
                self._right_resize_start_w = self.width()
                event.accept()
                return
            mods = QApplication.keyboardModifiers()
            add_to_selection = mods in (Qt.KeyboardModifier.ShiftModifier, Qt.KeyboardModifier.ControlModifier)
            self.clicked.emit(self, add_to_selection)
        super().mousePressEvent(event)
        event.accept()

    def mouseMoveEvent(self, event):
        if self._right_resizing:
            delta = event.globalPosition().toPoint().x() - self._right_resize_start_x
            new_w = max(200, self._right_resize_start_w + delta)
            parent = self.parent()
            if parent:
                max_w = parent.width() - self.x()
                new_w = min(new_w, max_w)
            self.setFixedWidth(new_w)
        elif event.position().toPoint().x() >= self.width() - 8:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._right_resizing:
            self._right_resizing = False
            self.save()
            return
        super().mouseReleaseEvent(event)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.drag_handle = DragHandle()

        default_header = self.block.header if self.block.header else self.block.block_type
        header_size = self.block.header_font_size or 9
        self._pending_header_font_size = None
        self._header_align_h = self.block.header_align_h
        self._header_align_v = self.block.header_align_v

        header_font = QFont("Segoe UI", header_size, QFont.Weight.DemiBold)
        single_line_h = max(20, int(header_size * 1.35 + 4))

        self._header_container = QWidget()
        self._header_container.setObjectName("header_container")
        self._header_v_layout = QVBoxLayout(self._header_container)
        self._header_v_layout.setContentsMargins(0, 0, 0, 0)
        self._header_v_layout.setSpacing(0)

        self._header_edit = QTextEdit()
        self._header_edit.setObjectName("block_header_edit")
        self._header_edit.setPlainText(default_header)
        self._header_edit.setPlaceholderText(self.block.block_type)
        self._header_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._header_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._header_edit.setTabChangesFocus(True)
        self._header_edit.setFont(header_font)
        self._header_edit.setFrameShape(QFrame.Shape.NoFrame)
        self._header_edit.setFixedHeight(single_line_h)
        self._header_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        _orig_header_focus = self._header_edit.focusInEvent
        def _on_header_focus(ev, orig=_orig_header_focus, me=self):
            orig(ev)
            me.header_focused.emit(me)
            QTimer.singleShot(0, me._apply_pending_header_font)
        self._header_edit.focusInEvent = _on_header_focus
        _orig_header_key = self._header_edit.keyPressEvent
        def _header_key(ev, orig=_orig_header_key, me=self):
            if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                ev.accept()
                me._header_edit.clearFocus()
            else:
                orig(ev)
        self._header_edit.keyPressEvent = _header_key
        self._header_edit.setStyleSheet(
            "QTextEdit { border: none; background: transparent; color: #9ca3af; }"
            "QTextEdit:focus { border: none; background: #f3f4f6; color: #374151; }"
        )

        self._apply_v_alignment_layout()

        h_align_map = {"left": Qt.AlignmentFlag.AlignLeft, "center": Qt.AlignmentFlag.AlignCenter, "right": Qt.AlignmentFlag.AlignRight}
        self._header_edit.setAlignment(h_align_map.get(self._header_align_h, Qt.AlignmentFlag.AlignLeft))

        container_h = self.block.header_height or max(36, int(header_size * 1.6 + 12))
        self._header_container.setFixedHeight(container_h)

        self._align_target_kind = "header"
        self._align_target_edit = self._header_edit

        self._h_align_group = QButtonGroup(self)
        self._h_left_btn = QPushButton("⫷")
        self._h_left_btn.setToolTip("Align left")
        self._h_center_btn = QPushButton("⫿")
        self._h_center_btn.setToolTip("Align center")
        self._h_right_btn = QPushButton("⫸")
        self._h_right_btn.setToolTip("Align right")
        for b in (self._h_left_btn, self._h_center_btn, self._h_right_btn):
            b.setCheckable(True)
            self._h_align_group.addButton(b)
        self._h_align_group.buttonClicked.connect(self._on_h_align_changed)

        self._v_align_group = QButtonGroup(self)
        self._v_top_btn = QPushButton("↥")
        self._v_top_btn.setToolTip("Align top")
        self._v_center_btn = QPushButton("↕")
        self._v_center_btn.setToolTip("Align middle")
        self._v_bottom_btn = QPushButton("↧")
        self._v_bottom_btn.setToolTip("Align bottom")
        for b in (self._v_top_btn, self._v_center_btn, self._v_bottom_btn):
            b.setCheckable(True)
            self._v_align_group.addButton(b)
        self._v_align_group.buttonClicked.connect(self._on_v_align_changed)

        self._apply_alignment_button_states()

        del_btn = QPushButton("×")
        del_btn.setFixedSize(24, 24)
        del_btn.setToolTip("Delete block")
        del_btn.setStyleSheet("QPushButton { border: 1px solid #e5e7eb; border-radius: 4px; color: #9ca3af; font-size: 14px; } QPushButton:hover { color: #ef4444; border-color: #ef4444; background: #fef2f2; }")

        header.addWidget(self.drag_handle)
        header.addWidget(self._header_container, 1)
        for b in (self._h_left_btn, self._h_center_btn, self._h_right_btn,
                  self._v_top_btn, self._v_center_btn, self._v_bottom_btn):
            header.addWidget(b)
        header.addWidget(del_btn)
        layout.addLayout(header)

        self._header_resize_handle = ResizeHandleHeader(self._header_container)
        layout.addWidget(self._header_resize_handle)

        self._body = None

        if self.block.block_type == "text":
            content_size = self.block.content_font_size or 13
            self._body = MarkdownBlock(self.block.id, self.block.content_markdown, content_font_size=content_size)
            self._body.changed.connect(self._on_content_changed)
            layout.addWidget(self._body)
            self._body.editor.focused.connect(lambda ed=self: self.content_focused.emit(ed))
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

        if self.block.height:
            self._apply_height(self.block.height)
        else:
            self._apply_height(60)

        if self.block.width:
            self.setFixedWidth(self.block.width)
        else:
            self.setMinimumWidth(260)

        del_btn.clicked.connect(self._delete)

    def _apply_height(self, h):
        h = max(60, h)
        if isinstance(self._body, MarkdownBlock):
            inner_h = max(30, h - 60)
            self._body.editor.setMinimumHeight(inner_h)
            self._body.preview.setMinimumHeight(inner_h)
        elif isinstance(self._body, TableWidget):
            for i in range(self._body.grid.count()):
                w = self._body.grid.itemAt(i)
                if w and w.widget() and isinstance(w.widget(), TableCell):
                    cell_h = max(30, (h - 80) // max(1, len(self._body.rows)))
                    w.widget().setMaximumHeight(cell_h + 20)
        self.setMinimumHeight(h)

    def _on_content_changed(self):
        self.changed.emit()

    def _delete(self):
        from src.undo_manager import _block_dict, _task_dict
        tasks_data = [_task_dict(t) for t in TaskRepo().get_by_block(self.block.id)]
        undo_manager.push({
            "type": "block",
            "block": _block_dict(self.block),
            "tasks": tasks_data,
        })
        BlockRepo().delete(self.block.id)
        self.delete_requested.emit(self)

    def _apply_pending_header_font(self):
        if self._pending_header_font_size:
            fmt = QTextCharFormat()
            fmt.setFontPointSize(self._pending_header_font_size)
            self._header_edit.setCurrentCharFormat(fmt)
            self._pending_header_font_size = None

    def _set_header_height_from_size(self, size):
        single = max(20, int(size * 1.35 + 4))
        self._header_edit.setFixedHeight(single)
        min_container = max(36, int(size * 1.6 + 12))
        current = self._header_container.height()
        if current < min_container:
            self._header_container.setFixedHeight(min_container)

    def _apply_v_alignment_layout(self):
        while self._header_v_layout.count():
            item = self._header_v_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        if self._header_align_v == "top":
            self._header_v_layout.addWidget(self._header_edit)
            self._header_v_layout.addStretch()
        elif self._header_align_v == "bottom":
            self._header_v_layout.addStretch()
            self._header_v_layout.addWidget(self._header_edit)
        else:
            self._header_v_layout.addStretch()
            self._header_v_layout.addWidget(self._header_edit)
            self._header_v_layout.addStretch()

    def _apply_alignment_button_states(self):
        h_map = {"left": self._h_left_btn, "center": self._h_center_btn, "right": self._h_right_btn}
        v_map = {"top": self._v_top_btn, "center": self._v_center_btn, "bottom": self._v_bottom_btn}
        self._h_align_group.blockSignals(True)
        self._v_align_group.blockSignals(True)
        btn = h_map.get(self._header_align_h)
        if btn:
            btn.setChecked(True)
        btn = v_map.get(self._header_align_v)
        if btn:
            btn.setChecked(True)
        self._h_align_group.blockSignals(False)
        self._v_align_group.blockSignals(False)

    def _set_align_target(self, kind, edit):
        self._align_target_kind = kind
        self._align_target_edit = edit
        self._sync_alignment_buttons()

    def _sync_alignment_buttons(self):
        kind, edit = self._align_target_kind, self._align_target_edit
        if not edit:
            return
        self._h_align_group.blockSignals(True)
        align = edit.alignment()
        if align & Qt.AlignmentFlag.AlignRight:
            self._h_right_btn.setChecked(True)
        elif align & Qt.AlignmentFlag.AlignCenter:
            self._h_center_btn.setChecked(True)
        else:
            self._h_left_btn.setChecked(True)
        self._h_align_group.blockSignals(False)
        self._v_align_group.blockSignals(True)
        hdr_kind = kind == "header"
        self._v_top_btn.setEnabled(hdr_kind)
        self._v_center_btn.setEnabled(hdr_kind)
        self._v_bottom_btn.setEnabled(hdr_kind)
        if hdr_kind:
            v_map = {"top": self._v_top_btn, "center": self._v_center_btn, "bottom": self._v_bottom_btn}
            btn = v_map.get(self._header_align_v)
            if btn:
                btn.setChecked(True)
        self._v_align_group.blockSignals(False)

    def _on_h_align_changed(self, btn):
        if btn == self._h_left_btn:
            align_val = Qt.AlignmentFlag.AlignLeft
            align_str = "left"
        elif btn == self._h_center_btn:
            align_val = Qt.AlignmentFlag.AlignCenter
            align_str = "center"
        elif btn == self._h_right_btn:
            align_val = Qt.AlignmentFlag.AlignRight
            align_str = "right"
        else:
            return
        if self._align_target_edit:
            self._align_target_edit.setAlignment(align_val)
        if self._align_target_kind == "header":
            self._header_align_h = align_str
            self.save()

    def _on_v_align_changed(self, btn):
        if btn == self._v_top_btn:
            self._header_align_v = "top"
        elif btn == self._v_center_btn:
            self._header_align_v = "center"
        elif btn == self._v_bottom_btn:
            self._header_align_v = "bottom"
        self._apply_v_alignment_layout()
        self.save()

    def save(self):
        self.block.pos_x = self.x()
        self.block.pos_y = self.y()
        self.block.height = self.minimumHeight() if self.minimumHeight() > 0 else None
        if self.minimumWidth() > 0 and self.minimumWidth() == self.maximumWidth():
            self.block.width = self.minimumWidth()
        else:
            self.block.width = None
        text = self._header_edit.toPlainText().strip()
        self.block.header = text if text and text != self.block.block_type else None
        self.block.header_font_size = self._header_edit.font().pointSize()
        self.block.header_align_h = self._header_align_h
        self.block.header_align_v = self._header_align_v
        self.block.header_height = self._header_container.height()
        if self._body and isinstance(self._body, MarkdownBlock):
            self.block.content_font_size = self._body.content_font_size
        if self.block.block_type == "table" and self._body:
            self.block.content_markdown = self._body.to_markdown()
            BlockRepo().update(self.block)
        elif self.block.block_type == "text" and self._body:
            self.block.content_markdown = self._body.editor.toHtml()
            BlockRepo().update(self.block)
        elif self.block.block_type in ("list", "checkbox"):
            BlockRepo().update(self.block)
        else:
            BlockRepo().update(self.block)
        self.saved.emit()


class Canvas(QWidget):
    clicked_at = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #ffffff;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked_at.emit(int(event.position().x()), int(event.position().y()))
        event.accept()
        super().mousePressEvent(event)


class PageEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page_id = None
        self.block_repo = BlockRepo()
        self._block_widgets: list[ContentBlockWidget] = []
        self._selected_block_widgets: set[ContentBlockWidget] = set()
        self._font_target: tuple[ContentBlockWidget, str] | None = None
        self.setStyleSheet("background: #ffffff;")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._build_toolbar(main_layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: #ffffff; }")

        self.content = Canvas()
        self.content.clicked_at.connect(self._on_canvas_clicked)
        self.scroll.setWidget(self.content)
        self.scroll.viewport().installEventFilter(self)
        self.scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)

        main_layout.addWidget(self.scroll, 1)

        self._drag_data = None  # (widget, start_x, start_y, start_mouse_x, start_mouse_y)
        self._canvas_click_pos: tuple[int, int] | None = None

        QApplication.instance().focusChanged.connect(self._on_focus_changed)

    def eventFilter(self, obj, event):
        if obj is self.scroll.viewport() and event.type() == QEvent.Type.Resize:
            self._update_canvas_size()
        return super().eventFilter(obj, event)

    def _update_canvas_size(self, extend=False):
        vp = self.scroll.viewport()
        vp_w = vp.width()
        max_bottom = 100
        for w in self._block_widgets:
            b = w.y() + w.height()
            if b > max_bottom:
                max_bottom = b
        desired_h = max(vp.height() + 300, max_bottom + 400)
        if extend:
            desired_h = max(desired_h, self.content.height() + 500)
        if desired_h != self.content.height() or vp_w != self.content.width():
            self.content.setFixedWidth(max(1, vp_w))
            self.content.resize(max(1, vp_w), desired_h)

    def _on_scroll(self, value):
        sb = self.scroll.verticalScrollBar()
        if sb.maximum() > 0 and value >= sb.maximum() - 300:
            self._update_canvas_size(extend=True)

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

        toolbar.addSpacing(8)
        toolbar.addWidget(QLabel("Size:"))
        self._font_size_combo = QComboBox()
        self._font_size_combo.addItems([str(s) for s in [9, 10, 11, 12, 13, 14, 15, 16, 18, 20, 22, 24, 28, 32]])
        self._font_size_combo.setCurrentText("13")
        self._font_size_combo.setFixedWidth(60)
        self._font_size_combo.setToolTip("Font size for focused header or text")
        tracer = self  # capture self for the lambda
        self._font_size_combo.currentTextChanged.connect(self._on_font_size_changed)
        toolbar.addWidget(self._font_size_combo)

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

    @staticmethod
    def _find_block_widget(widget):
        while widget:
            if isinstance(widget, ContentBlockWidget):
                return widget
            widget = widget.parent()
        return None

    def _set_font_combo_from_target(self):
        if not self._font_target:
            return
        block_w, part = self._font_target
        if part == "header":
            cursor = block_w._header_edit.textCursor()
            pt = cursor.charFormat().fontPointSize()
            size = int(pt) if pt >= 1 else block_w._header_edit.font().pointSize()
        elif part == "list_item":
            line = getattr(block_w, '_active_line', None)
            size = line.font().pointSize() if line else 13
        elif part == "table_cell":
            cell = getattr(block_w, '_active_cell', None)
            if cell:
                cursor = cell.textCursor()
                pt = cursor.charFormat().fontPointSize()
                size = int(pt) if pt >= 1 else cell.font().pointSize() or 13
            else:
                size = 13
        else:
            try:
                size = block_w._body.content_font_size
            except AttributeError:
                return
        self._font_size_combo.blockSignals(True)
        self._font_size_combo.setCurrentText(str(size))
        self._font_size_combo.blockSignals(False)

    def _on_block_header_focused(self, block_w):
        self._font_target = (block_w, "header")
        self._set_font_combo_from_target()

    def _on_block_content_focused(self, block_w):
        self._font_target = (block_w, "content")
        self._set_font_combo_from_target()

    def _on_focus_changed(self, old, new):
        if not new:
            return
        block_w = self._find_block_widget(new)
        if not block_w:
            return
        if isinstance(new, QTextEdit) and new.objectName() == "block_header_edit":
            self._font_target = (block_w, "header")
            self._set_font_combo_from_target()
            block_w._set_align_target("header", block_w._header_edit)
        elif isinstance(new, QLineEdit) and hasattr(block_w, '_body') and isinstance(block_w._body, TaskWidget):
            block_w._active_line = new
            self._font_target = (block_w, "list_item")
            self._set_font_combo_from_target()
        elif isinstance(new, TableCell):
            block_w._active_cell = new
            self._font_target = (block_w, "table_cell")
            self._set_font_combo_from_target()
            block_w._set_align_target("table_cell", new)
        elif isinstance(new, (MarkdownTextEdit, QTextBrowser)):
            try:
                self._font_target = (block_w, "content")
                self._set_font_combo_from_target()
            except AttributeError:
                pass
            block_w._set_align_target("content", block_w._body.editor)

    def _on_font_size_changed(self, val_str):
        if not self._font_target:
            return
        try:
            size = int(val_str)
        except (ValueError, TypeError):
            return
        block_w, part = self._font_target
        if part == "header":
            cursor = block_w._header_edit.textCursor()
            if cursor.hasSelection():
                fmt = QTextCharFormat()
                fmt.setFontPointSize(size)
                cursor.mergeCharFormat(fmt)
            else:
                fmt = QTextCharFormat()
                fmt.setFontPointSize(size)
                block_w._header_edit.setCurrentCharFormat(fmt)
                block_w._pending_header_font_size = size
            block_w._set_header_height_from_size(size)
            block_w.block.header_font_size = size
            block_w.save()
        elif part == "list_item":
            line = getattr(block_w, '_active_line', None)
            if line:
                font = line.font()
                font.setPointSize(size)
                line.setFont(font)
        elif part == "table_cell":
            cell = getattr(block_w, '_active_cell', None)
            if cell:
                cursor = cell.textCursor()
                if cursor.hasSelection():
                    fmt = QTextCharFormat()
                    fmt.setFontPointSize(size)
                    cursor.mergeCharFormat(fmt)
                else:
                    fmt = QTextCharFormat()
                    fmt.setFontPointSize(size)
                    cell.setCurrentCharFormat(fmt)
        elif part == "content":
            try:
                block_w._body.set_content_font_size(size)
            except AttributeError:
                return
            block_w.block.content_font_size = size
            block_w.save()

    def _get_active_text_block(self):
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
        self._clear_selection()

        for w in self._block_widgets:
            w.setParent(None)
            w.deleteLater()
        self._block_widgets.clear()

        blocks = self.block_repo.get_by_page(page_id)

        all_at_zero = all(b.pos_x == 0 and b.pos_y == 0 for b in blocks)

        for i, block in enumerate(blocks):
            if all_at_zero:
                block.pos_x = 30 + (i % 5) * 280
                block.pos_y = 30 + (i // 5) * 200
            w = ContentBlockWidget(block, index=i)
            w.changed.connect(self._on_block_changed)
            w.delete_requested.connect(self._on_block_deleted)
            w.clicked.connect(self._on_block_clicked)
            w.header_focused.connect(self._on_block_header_focused)
            w.content_focused.connect(self._on_block_content_focused)
            self._setup_drag(w)
            w.saved.connect(self._update_canvas_size)
            w.setParent(self.content)
            w.move(block.pos_x, block.pos_y)
            w.show()
            self._block_widgets.append(w)
        self._update_canvas_size()

    def _setup_drag(self, widget):
        orig_mouse_press = widget.drag_handle.mousePressEvent
        def _drag_press(ev, w=widget):
            if ev.button() == Qt.MouseButton.LeftButton:
                self._drag_data = (w, w.x(), w.y(), ev.globalPosition().toPoint().x(), ev.globalPosition().toPoint().y())
                w.raise_()
                ev.accept()
            else:
                orig_mouse_press(ev)
        widget.drag_handle.mousePressEvent = _drag_press
        orig_mouse_move = widget.drag_handle.mouseMoveEvent
        def _drag_move(ev, w=widget):
            if self._drag_data and self._drag_data[0] is w:
                dx = ev.globalPosition().toPoint().x() - self._drag_data[3]
                dy = ev.globalPosition().toPoint().y() - self._drag_data[4]
                new_x = max(0, self._drag_data[1] + dx)
                new_y = self._drag_data[2] + dy
                max_x = self.content.width() - w.width()
                if new_x > max_x:
                    new_x = max_x
                w.move(new_x, new_y)
                ev.accept()
            else:
                orig_mouse_move(ev)
        widget.drag_handle.mouseMoveEvent = _drag_move
        orig_mouse_release = widget.drag_handle.mouseReleaseEvent
        def _drag_release(ev, w=widget):
            if self._drag_data and self._drag_data[0] is w:
                w.block.pos_x = w.x()
                w.block.pos_y = w.y()
                w.save()
                self._drag_data = None
                ev.accept()
            else:
                orig_mouse_release(ev)
        widget.drag_handle.mouseReleaseEvent = _drag_release

    def _on_block_changed(self):
        pass

    def _on_block_deleted(self, widget):
        if widget in self._block_widgets:
            self._block_widgets.remove(widget)
            widget.setParent(None)
            widget.deleteLater()

    def _on_block_clicked(self, widget, add_to_selection):
        widget.raise_()
        if add_to_selection:
            if widget in self._selected_block_widgets:
                widget.set_selected(False)
                self._selected_block_widgets.discard(widget)
            else:
                widget.set_selected(True)
                self._selected_block_widgets.add(widget)
        else:
            self._clear_selection()
            widget.set_selected(True)
            self._selected_block_widgets.add(widget)

    def _clear_selection(self):
        for w in self._selected_block_widgets:
            w.set_selected(False)
        self._selected_block_widgets.clear()

    def _delete_selected_blocks(self):
        if not self._selected_block_widgets:
            return
        from src.undo_manager import _block_dict, _task_dict
        from src.repositories.task_repo import TaskRepo
        for w in list(self._selected_block_widgets):
            tasks_data = [_task_dict(t) for t in TaskRepo().get_by_block(w.block.id)]
            undo_manager.push({
                "type": "block",
                "block": _block_dict(w.block),
                "tasks": tasks_data,
            })
            BlockRepo().delete(w.block.id)
        self._clear_selection()
        self.load_page(self.current_page_id)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self._delete_selected_blocks()
            event.accept()
        elif event.key() == Qt.Key.Key_D and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            focus_widget = QApplication.focusWidget()
            if focus_widget and isinstance(focus_widget, (QTextEdit, QLineEdit)):
                event.ignore()
                return
            self._delete_selected_blocks()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _scroll_to_newest_block(self):
        if self._block_widgets:
            self.scroll.ensureWidgetVisible(self._block_widgets[-1], 50, 50)

    def _on_canvas_clicked(self, x, y):
        self._canvas_click_pos = (x, y)

    def _add_block(self, block_type: str):
        if not self.current_page_id:
            return
        try:
            if self._canvas_click_pos is not None:
                pos_x, pos_y = self._canvas_click_pos
                self._canvas_click_pos = None
            else:
                max_bottom = 50
                for w in self._block_widgets:
                    b = w.y() + w.height()
                    if b > max_bottom:
                        max_bottom = b
                pos_x = 50
                pos_y = max_bottom + 20
            block = ContentBlock(
                page_id=self.current_page_id,
                block_type=block_type,
                pos_x=pos_x,
                pos_y=pos_y,
            )
            self.block_repo.create(block)
            self.load_page(self.current_page_id)
            QTimer.singleShot(0, self._scroll_to_newest_block)
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to add block:\n{e}")

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
        for w in self._block_widgets:
            if hasattr(w, 'save'):
                w.save()
