import json
import traceback
from datetime import datetime, timedelta

import markdown
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout,
    QComboBox, QLabel, QCheckBox, QGridLayout, QLineEdit,
    QScrollArea, QDialog, QDialogButtonBox, QMessageBox,
    QListWidget, QFrame, QTextBrowser, QSizePolicy,
    QToolButton, QApplication, QLayout, QWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint, QMimeData, QSize, QRect
from PyQt6.QtGui import (
    QFont, QAction, QKeySequence, QTextCursor, QTextCharFormat, QDrag,
    QPainter, QColor, QBrush, QPen
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

    def set_content_font_size(self, size):
        self.content_font_size = size
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            fmt.setFontPointSize(size)
            cursor.mergeCharFormat(fmt)
        else:
            font = self.editor.document().defaultFont()
            font.setPointSize(size)
            self.editor.document().setDefaultFont(font)
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
            new_h = max(60, self._start_height + delta_y)
            if self._in_corner:
                delta_x = event.globalPosition().toPoint().x() - self._start_x
                new_w = max(200, self._start_width + delta_x)
                self.block_widget.setFixedWidth(new_w)
                self.block_widget.setFixedHeight(new_h)
            else:
                self.block_widget.setMinimumHeight(new_h)
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


class ContentBlockWidget(QFrame):
    changed = pyqtSignal()
    delete_requested = pyqtSignal(object)
    clicked = pyqtSignal(object, bool)  # (self, add_to_selection)
    header_focused = pyqtSignal(object)  # self
    content_focused = pyqtSignal(object)  # self

    def __init__(self, block: ContentBlock, index=0, parent=None):
        super().__init__(parent)
        self.block = block
        self.block_index = index
        self._selected = False
        self.setObjectName("block")
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet(BLOCK_STYLE)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self._build_ui()

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            mods = QApplication.keyboardModifiers()
            add_to_selection = mods in (Qt.KeyboardModifier.ShiftModifier, Qt.KeyboardModifier.ControlModifier)
            self.clicked.emit(self, add_to_selection)
        super().mousePressEvent(event)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.drag_handle = DragHandle()

        default_header = self.block.header if self.block.header else self.block.block_type
        header_size = self.block.header_font_size or 9
        self._header_edit = QLineEdit(default_header)
        self._header_edit.setPlaceholderText(self.block.block_type)
        header_font = QFont("Segoe UI", header_size, QFont.Weight.DemiBold)
        self._header_edit.setFont(header_font)
        _orig_header_focus = self._header_edit.focusInEvent
        def _on_header_focus(ev, orig=_orig_header_focus, me=self):
            orig(ev)
            me.header_focused.emit(me)
        self._header_edit.focusInEvent = _on_header_focus
        self._header_edit.setStyleSheet(
            "QLineEdit { border: none; background: transparent; color: #9ca3af; padding: 0; }"
            "QLineEdit:focus { border: none; background: #f3f4f6; color: #374151; }"
        )

        del_btn = QPushButton("×")
        del_btn.setFixedSize(24, 24)
        del_btn.setToolTip("Delete block")
        del_btn.setStyleSheet("QPushButton { border: 1px solid #e5e7eb; border-radius: 4px; color: #9ca3af; font-size: 14px; } QPushButton:hover { color: #ef4444; border-color: #ef4444; background: #fef2f2; }")

        header.addWidget(self.drag_handle)
        header.addWidget(self._header_edit, 1)
        header.addStretch()
        header.addWidget(del_btn)
        layout.addLayout(header)

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

    def save(self):
        self.block.height = self.minimumHeight() if self.minimumHeight() > 0 else None
        if self.minimumWidth() > 0 and self.minimumWidth() == self.maximumWidth():
            self.block.width = self.minimumWidth()
        else:
            self.block.width = None
        text = self._header_edit.text().strip()
        self.block.header = text if text and text != self.block.block_type else None
        self.block.header_font_size = self._header_edit.font().pointSize()
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


class DropIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)
        self.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setPen(QPen(QColor("#6366f1"), 2))
        p.drawLine(0, 2, self.width(), 2)


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, hspacing=6, vspacing=4):
        super().__init__(parent)
        self._items = []
        self._hspacing = hspacing
        self._vspacing = vspacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def removeWidget(self, widget):
        for i, item in enumerate(self._items):
            if item.widget() == widget:
                self._items.pop(i)
                break

    def insertWidget(self, index, widget):
        item = QWidgetItem(widget)
        self._items.insert(index, item)

    def expandingDirections(self):
        return Qt.Orientation.Horizontal

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True).height()

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return QSize(400, 200)

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            hint = item.minimumSize()
            size = size.expandedTo(hint)
        margins = self.contentsMargins()
        size += QSize(2 * margins.left(), 2 * margins.top())
        return size

    def _item_width(self, item):
        widget = item.widget()
        if not widget:
            return 250
        min_w = widget.minimumWidth()
        max_w = widget.maximumWidth()
        if min_w > 0 and min_w == max_w:
            return min_w
        if min_w > 0:
            return min_w
        return max(200, item.sizeHint().width())

    def _is_fixed_width(self, item):
        widget = item.widget()
        if not widget:
            return False
        min_w = widget.minimumWidth()
        max_w = widget.maximumWidth()
        return min_w > 0 and min_w == max_w

    def _item_height(self, item):
        widget = item.widget()
        if not widget:
            return 100
        if widget.minimumHeight() > 0:
            return widget.minimumHeight()
        return max(item.sizeHint().height(), 60)

    def _do_layout(self, rect, test_only):
        margins = self.contentsMargins()
        content_left = rect.x() + margins.left()
        content_top = rect.y() + margins.top()
        content_width = max(1, rect.width() - margins.left() - margins.right())

        visible = [item for item in self._items if item.widget()]

        rows = []
        current_row = []
        current_row_width = 0

        for item in visible:
            is_fixed = self._is_fixed_width(item)
            if is_fixed and current_row:
                sep = self._hspacing
                iw = self._item_width(item)
                if current_row_width + sep + iw <= content_width:
                    current_row.append(item)
                    current_row_width += sep + iw
                    continue
                rows.append(current_row)
                current_row = [item]
                current_row_width = iw
            elif is_fixed and not current_row:
                current_row.append(item)
                current_row_width = self._item_width(item)
            else:
                if current_row:
                    rows.append(current_row)
                current_row = [item]
                current_row_width = self._item_width(item)

        if current_row:
            rows.append(current_row)

        y = content_top
        for row in rows:
            total_fixed = 0
            stretch_indices = []
            for idx, item in enumerate(row):
                widget = item.widget()
                if not widget or widget.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding:
                    stretch_indices.append(idx)
                else:
                    total_fixed += self._item_width(item)

            spacing = self._hspacing * (len(row) - 1)
            stretch_avail = max(0, content_width - total_fixed - spacing)
            stretch_w = stretch_avail // max(1, len(stretch_indices)) if stretch_indices else 0
            remaining = stretch_avail - stretch_w * len(stretch_indices) if stretch_indices else 0

            x = content_left
            max_h = 0
            for idx, item in enumerate(row):
                if idx in stretch_indices:
                    w = stretch_w + (1 if idx < remaining else 0)
                else:
                    w = self._item_width(item)
                h = self._item_height(item)
                if not test_only:
                    item.setGeometry(QRect(x, y, max(1, w), max(1, h)))
                x += w + self._hspacing
                max_h = max(max_h, h)

            y += max_h + self._vspacing

        total_height = y - content_top + margins.bottom()
        return QSize(content_width, total_height)


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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: #ffffff; }")

        self.content = QWidget()
        self.content.setStyleSheet("background: #ffffff;")
        self.content_layout = FlowLayout(self.content, margin=12)
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

        QApplication.instance().focusChanged.connect(self._on_focus_changed)

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
            size = block_w._header_edit.font().pointSize()
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
        if new is block_w._header_edit:
            self._font_target = (block_w, "header")
            self._set_font_combo_from_target()
        elif isinstance(new, (MarkdownTextEdit, QTextBrowser)):
            try:
                self._font_target = (block_w, "content")
                self._set_font_combo_from_target()
            except AttributeError:
                pass

    def _on_font_size_changed(self, val_str):
        if not self._font_target:
            return
        try:
            size = int(val_str)
        except (ValueError, TypeError):
            return
        block_w, part = self._font_target
        if part == "header":
            font = block_w._header_edit.font()
            font.setPointSize(size)
            block_w._header_edit.setFont(font)
        elif part == "content":
            try:
                block_w._body.set_content_font_size(size)
            except AttributeError:
                return

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

        for i, block in enumerate(blocks):
            w = ContentBlockWidget(block, index=i)
            w.changed.connect(self._on_block_changed)
            w.delete_requested.connect(self._on_block_deleted)
            w.clicked.connect(self._on_block_clicked)
            w.header_focused.connect(self._on_block_header_focused)
            w.content_focused.connect(self._on_block_content_focused)
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

    def _on_block_clicked(self, widget, add_to_selection):
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

    def _add_block(self, block_type: str):
        if not self.current_page_id:
            return
        try:
            block = ContentBlock(page_id=self.current_page_id, block_type=block_type)
            self.block_repo.create(block)
            self.load_page(self.current_page_id)
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to add block:\n{e}")

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
        for w in self._block_widgets:
            if hasattr(w, 'save'):
                w.save()
