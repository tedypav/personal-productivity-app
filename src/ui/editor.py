import json
import os
import traceback
import uuid
from datetime import datetime, timedelta

import markdown  # type: ignore[import-untyped]
from PyQt6.QtCore import QEvent, QSize, Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QFont,
    QIcon,
    QImage,
    QPainter,
    QPixmap,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextImageFormat,
    QTextListFormat,
)
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QTextBrowser,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.models.content_block import ContentBlock
from src.models.task import Task
from src.repositories.block_repo import BlockRepo
from src.repositories.task_repo import TaskRepo
from src.repositories.template_repo import TemplateRepo
from src.undo_manager import undo_manager

MD_EXTENSIONS = ["fenced_code", "tables", "nl2br"]


def render_markdown(text: str, font_size: int = 13) -> str:
    html = markdown.markdown(text, extensions=MD_EXTENSIONS)
    return (
        f'<html><body style="font-family:Segoe UI, sans-serif; '
        f'padding:4px 8px; line-height:1.4; font-size:{font_size}px;">'
        f"{html}</body></html>"
    )


BLOCK_STYLE = """
QFrame#block {
    background: #FFFFFF;
    border: 1px solid #F0E6E8;
    border-radius: 12px;
}
QFrame#block:hover {
    border-color: #F7D1DC;
}
QFrame#block[selected="true"] {
    border: 2px solid #CFA6D6;
    background: #FFFBFD;
}
"""


def _get_edit_html_body(edit):
    html = edit.toHtml()
    import re

    body_match = re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL)
    if body_match:
        return body_match.group(1).strip()
    return html


def _apply_format_to_edit(edit, fmt_name, parent_widget=None):
    try:
        cursor = edit.textCursor()
    except Exception:
        return
    try:
        if fmt_name == "bold":
            if cursor.hasSelection():
                fmt = QTextCharFormat()
                current_weight = cursor.charFormat().fontWeight()
                fmt.setFontWeight(
                    QFont.Weight.Normal
                    if current_weight >= QFont.Weight.Bold
                    else QFont.Weight.Bold
                )
                cursor.mergeCharFormat(fmt)
            else:
                fmt = cursor.charFormat()
                fmt.setFontWeight(
                    QFont.Weight.Normal
                    if fmt.fontWeight() >= QFont.Weight.Bold
                    else QFont.Weight.Bold
                )
                cursor.setCharFormat(fmt)
        elif fmt_name == "italic":
            if cursor.hasSelection():
                fmt = QTextCharFormat()
                fmt.setFontItalic(not cursor.charFormat().fontItalic())
                cursor.mergeCharFormat(fmt)
            else:
                fmt = cursor.charFormat()
                fmt.setFontItalic(not fmt.fontItalic())
                cursor.setCharFormat(fmt)
        elif fmt_name == "h1":
            if cursor.hasSelection():
                fmt = QTextCharFormat()
                char_fmt = cursor.charFormat()
                pt = char_fmt.fontPointSize()
                if pt < 1:
                    pt = edit.font().pointSize()
                if pt >= 19 and char_fmt.fontWeight() >= QFont.Weight.Bold:
                    fmt.setFontPointSize(13)
                    fmt.setFontWeight(QFont.Weight.Normal)
                else:
                    fmt.setFontPointSize(20)
                    fmt.setFontWeight(QFont.Weight.Bold)
                cursor.mergeCharFormat(fmt)
            else:
                fmt = cursor.charFormat()
                pt = fmt.fontPointSize()
                if pt < 1:
                    pt = edit.font().pointSize()
                if pt >= 19 and fmt.fontWeight() >= QFont.Weight.Bold:
                    fmt.setFontPointSize(13)
                    fmt.setFontWeight(QFont.Weight.Normal)
                else:
                    fmt.setFontPointSize(20)
                    fmt.setFontWeight(QFont.Weight.Bold)
                cursor.setCharFormat(fmt)
        elif fmt_name == "h2":
            if cursor.hasSelection():
                fmt = QTextCharFormat()
                char_fmt = cursor.charFormat()
                pt = char_fmt.fontPointSize()
                if pt < 1:
                    pt = edit.font().pointSize()
                if 15 <= pt < 19 and char_fmt.fontWeight() >= QFont.Weight.Bold:
                    fmt.setFontPointSize(13)
                    fmt.setFontWeight(QFont.Weight.Normal)
                else:
                    fmt.setFontPointSize(16)
                    fmt.setFontWeight(QFont.Weight.Bold)
                cursor.mergeCharFormat(fmt)
            else:
                fmt = cursor.charFormat()
                pt = fmt.fontPointSize()
                if pt < 1:
                    pt = edit.font().pointSize()
                if 15 <= pt < 19 and fmt.fontWeight() >= QFont.Weight.Bold:
                    fmt.setFontPointSize(13)
                    fmt.setFontWeight(QFont.Weight.Normal)
                else:
                    fmt.setFontPointSize(16)
                    fmt.setFontWeight(QFont.Weight.Bold)
                cursor.setCharFormat(fmt)
        elif fmt_name == "code":
            fmt = QTextCharFormat()
            fmt.setFontFamily("Consolas")
            fmt.setBackground(QColor("#f3f4f6"))
            cursor.mergeCharFormat(fmt)
        elif fmt_name == "link":
            _insert_link_dialog(edit, parent_widget)
        elif fmt_name == "bullet":
            _toggle_bullet(cursor, edit)
        elif fmt_name == "attach":
            _attach_file(edit, parent_widget)
    except Exception as e:
        print(f"Error applying format '{fmt_name}': {e}")


def _insert_link_dialog(edit, parent_widget=None):
    cursor = edit.textCursor()
    selected = cursor.selectedText()
    url, ok = QInputDialog.getText(
        parent_widget or edit,
        "Insert Link",
        "URL:",
        QLineEdit.EchoMode.Normal,
        "https://",
    )
    if not ok or not url.strip():
        return
    url = url.strip()
    if selected:
        fmt = QTextCharFormat()
        fmt.setAnchor(True)
        fmt.setAnchorHref(url)
        fmt.setForeground(QColor("#4f46e5"))
        fmt.setFontUnderline(True)
        cursor.mergeCharFormat(fmt)
    else:
        fmt = QTextCharFormat()
        fmt.setAnchor(True)
        fmt.setAnchorHref(url)
        fmt.setForeground(QColor("#4f46e5"))
        fmt.setFontUnderline(True)
        cursor.insertText(url, fmt)


def _insert_bullet(cursor, edit):
    """Insert a bullet list at the current cursor position."""
    try:
        list_fmt = QTextListFormat()
        list_fmt.setStyle(QTextListFormat.Style.ListDisc)
        list_fmt.setIndent(1)
        cursor.createList(list_fmt)
        edit.setTextCursor(cursor)
    except Exception as e:
        print(f"Error creating bullet list: {e}")


def _toggle_bullet(cursor, edit):
    """Toggle bullet list on/off at current cursor position.

    - Empty block with bullet: remove it
    - Block without bullet: add one
    - Non-empty block already in list: do nothing
    """
    try:
        block = cursor.block()
        if not block.isValid():
            return

        text_list = block.textList()
        has_text = bool(block.text().strip())

        if text_list and text_list.format().style() == QTextListFormat.Style.ListDisc:
            if has_text:
                return
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            new_fmt = QTextBlockFormat()
            cursor.setBlockFormat(new_fmt)
            cursor.clearSelection()
            edit.setTextCursor(cursor)
        else:
            _insert_bullet(cursor, edit)
    except Exception as e:
        print(f"Error toggling bullet list: {e}")


def _attach_file(edit, parent_widget=None):
    file_path, _ = QFileDialog.getOpenFileName(
        parent_widget or edit,
        "Attach File",
        "",
        "All Files (*);;"
        "Images (*.png *.jpg *.jpeg *.gif *.bmp *.svg);;"
        "Documents (*.pdf *.doc *.docx *.txt)",
    )
    if not file_path:
        return
    cursor = edit.textCursor()
    _embed_file_at_cursor(cursor, file_path, edit)


def _embed_file_at_cursor(cursor, file_path, edit):
    ext = os.path.splitext(file_path)[1].lower()
    image_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp"}
    if ext in image_exts:
        img = QImage(file_path)
        if not img.isNull():
            doc = edit.document()
            img_name = f"img_{uuid.uuid4().hex}{ext}"
            doc.addResource(
                QTextDocument.ResourceType.ImageResource, QUrl(img_name), img
            )
            img_fmt = QTextImageFormat()
            max_w = (
                min(img.width(), edit.viewport().width() - 40)
                if edit.viewport().width() > 60
                else img.width()
            )
            if img.width() > max_w:
                ratio = max_w / img.width()
                img_fmt.setWidth(int(max_w))
                img_fmt.setHeight(int(img.height() * ratio))
            else:
                img_fmt.setWidth(img.width())
                img_fmt.setHeight(img.height())
            img_fmt.setName(img_name)
            cursor.insertImage(img_fmt)
            return
    display_name = os.path.basename(file_path)
    fmt = QTextCharFormat()
    fmt.setAnchor(True)
    fmt.setAnchorHref(file_path)
    fmt.setForeground(QColor("#4f46e5"))
    fmt.setFontUnderline(True)
    cursor.insertText(f"[{display_name}]", fmt)


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
            html = markdown.markdown(
                content, extensions=["fenced_code", "tables", "nl2br"]
            )
            wrapped = (
                '<html><body style="font-family:Segoe UI, sans-serif; '
                f'font-size:13px;">{html}</body></html>'
            )
            self.setHtml(wrapped)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focused.emit()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_lost.emit()

    def insertFromMimeData(self, source):
        if source and source.hasImage():
            img = source.imageData()
            if isinstance(img, QImage) and not img.isNull():
                cursor = self.textCursor()
                doc = self.document()
                img_name = f"img_{uuid.uuid4().hex}.png"
                doc.addResource(
                    QTextDocument.ResourceType.ImageResource, QUrl(img_name), img
                )
                img_fmt = QTextImageFormat()
                max_w = (
                    min(img.width(), self.viewport().width() - 40)
                    if self.viewport().width() > 60
                    else img.width()
                )
                if img.width() > max_w:
                    ratio = max_w / img.width()
                    img_fmt.setWidth(int(max_w))
                    img_fmt.setHeight(int(img.height() * ratio))
                else:
                    img_fmt.setWidth(img.width())
                    img_fmt.setHeight(img.height())
                img_fmt.setName(img_name)
                cursor.insertImage(img_fmt)
                return
        super().insertFromMimeData(source)


class FormattedTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)

    def insertFromMimeData(self, source):
        if source and source.hasImage():
            img = source.imageData()
            if isinstance(img, QImage) and not img.isNull():
                cursor = self.textCursor()
                doc = self.document()
                img_name = f"img_{uuid.uuid4().hex}.png"
                doc.addResource(
                    QTextDocument.ResourceType.ImageResource, QUrl(img_name), img
                )
                img_fmt = QTextImageFormat()
                max_w = (
                    min(img.width(), self.viewport().width() - 40)
                    if self.viewport().width() > 60
                    else img.width()
                )
                if img.width() > max_w:
                    ratio = max_w / img.width()
                    img_fmt.setWidth(int(max_w))
                    img_fmt.setHeight(int(img.height() * ratio))
                else:
                    img_fmt.setWidth(img.width())
                    img_fmt.setHeight(img.height())
                img_fmt.setName(img_name)
                cursor.insertImage(img_fmt)
                return
        super().insertFromMimeData(source)


class _EmbeddedTaskContainer(QWidget):
    """Container for one embedded task list inside a text block or table cell."""

    remove_requested = pyqtSignal(object)

    def __init__(self, task_widget, parent=None):
        super().__init__(parent)
        self.task_widget = task_widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 4)
        layout.setSpacing(0)

        # Top handle bar: drag handle + remove button
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(0)

        self.drag_handle = QLabel("⠿")
        self.drag_handle.setFixedWidth(20)
        self.drag_handle.setCursor(Qt.CursorShape.OpenHandCursor)
        self.drag_handle.setStyleSheet("color: #9ca3af; font-size: 14px;")
        self.drag_handle.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        lbl = QLabel("Tasks")
        lbl.setStyleSheet(
            "color: #6b7280; font-size: 11px; font-weight: bold; padding: 0 4px;"
        )

        self._add_btn = QPushButton("+ Add Task")
        self._add_btn.setFixedHeight(22)
        self._add_btn.setStyleSheet(
            "QPushButton { font-size: 11px; border: 1px solid #d1d5db;"
            " border-radius: 3px; background: #f9fafb; padding: 0 8px;"
            " color: #374151; }"
            " QPushButton:hover { border-color: #6366f1; color: #6366f1; }"
        )

        self._remove_btn = QPushButton("×")
        self._remove_btn.setFixedSize(20, 20)
        self._remove_btn.setStyleSheet(
            "QPushButton { border: none; font-size: 14px; color: #9ca3af; }"
            " QPushButton:hover { color: #ef4444; }"
            " QToolTip { background-color: #FFFFFF; color: #2E2B2B;"
            " border: 1px solid #F0E6E8; border-radius: 8px;"
            " padding: 6px 10px; font-size: 12px; }"
        )
        self._remove_btn.setToolTip("Remove this task list")

        top_bar.addWidget(self.drag_handle)
        top_bar.addWidget(lbl)
        top_bar.addStretch()
        top_bar.addWidget(self._add_btn)
        top_bar.addSpacing(4)
        top_bar.addWidget(self._remove_btn)

        layout.addLayout(top_bar)
        layout.addWidget(task_widget)

        self._add_btn.clicked.connect(task_widget._add_task)
        self._remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))

        self.setStyleSheet("""
            _EmbeddedTaskContainer {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background: #ffffff;
            }
        """)


class MarkdownBlock(QWidget):
    changed = pyqtSignal()
    embedded_changed = pyqtSignal()
    editing_changed = pyqtSignal(bool)

    def __init__(self, block_id, content="", parent=None, content_font_size=None):
        super().__init__(parent)
        self.block_id = block_id
        self.editing = False
        self.content_font_size = (
            content_font_size if content_font_size and content_font_size >= 1 else 13
        )
        self._embedded_lists = []
        self._embedded_id_counter = -1
        self._active_list = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        text_content = self._extract_text_content(content)
        self.editor = MarkdownTextEdit(block_id, text_content)
        self.editor.setVisible(False)
        self.editor.focus_lost.connect(self._on_focus_lost)

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
        self.editor.focused.connect(
            lambda: QTimer.singleShot(0, self._apply_pending_font)
        )

        self._text_stack = QStackedWidget()
        self._text_stack.addWidget(self.preview)
        self._text_stack.addWidget(self.editor)
        self._text_stack.setCurrentWidget(self.preview)
        layout.addWidget(self._text_stack)

        self._embedded_container = QWidget()
        self._embedded_layout = QVBoxLayout(self._embedded_container)
        self._embedded_layout.setContentsMargins(0, 0, 0, 0)
        self._embedded_layout.setSpacing(4)
        layout.addWidget(self._embedded_container)

        self._update_preview()
        self.setStyleSheet("""
            QTextBrowser { background: transparent; border: none; }
            QTextEdit { border: 1px solid #F0E6E8; border-radius: 10px; }
            QTextEdit:focus { border-color: #CFA6D6; }
        """)

        self._load_embedded_lists(content)

    @staticmethod
    def _extract_text_content(content):
        if content and content.startswith("{"):
            try:
                data = json.loads(content)
                if isinstance(data, dict) and "text" in data:
                    return data["text"]
            except (json.JSONDecodeError, TypeError):
                pass
        return content

    def _load_embedded_lists(self, content):
        if not content or not content.startswith("{"):
            return
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return
        if not isinstance(data, dict) or "task_lists" not in data:
            return
        text_content = data.get("text", "")
        if text_content:
            self.editor.blockSignals(True)
            self.editor.setHtml(text_content)
            self.editor.blockSignals(False)
        for task_list in data["task_lists"]:
            self._restore_embedded_list(task_list)

    def _next_embedded_id(self):
        eid = self._embedded_id_counter
        self._embedded_id_counter -= 1
        return eid

    def _restore_embedded_list(self, tasks_data):
        eid = self._next_embedded_id()
        from src.repositories.in_memory_task_repo import InMemoryTaskRepo

        repo = InMemoryTaskRepo()
        for td in tasks_data:
            from src.models.task import Task

            task = Task(
                content_block_id=eid,
                text=td.get("text", ""),
                is_checked=td.get("is_checked", False),
                recurrence_type=td.get("recurrence_type", "none"),
                due_date=td.get("due_date"),
            )
            repo.create(task)
        tw = TaskWidget(eid, parent=self, task_repo=repo)
        tw.task_changed.connect(self._on_embedded_task_changed)
        container = _EmbeddedTaskContainer(tw, self)
        container.remove_requested.connect(self._remove_embedded_list)
        self._embedded_layout.addWidget(container)
        self._embedded_lists.append(
            {"id": eid, "repo": repo, "tw": tw, "container": container}
        )

    def add_task_list(self):
        try:
            eid = self._next_embedded_id()
            from src.repositories.in_memory_task_repo import InMemoryTaskRepo

            repo = InMemoryTaskRepo()
            from src.models.task import Task

            task = Task(content_block_id=eid, text="New task")
            repo.create(task)
            tw = TaskWidget(eid, parent=self, task_repo=repo)
            tw.task_changed.connect(self._on_embedded_task_changed)
            container = _EmbeddedTaskContainer(tw, self)
            container.remove_requested.connect(self._remove_embedded_list)
            self._embedded_layout.addWidget(container)
            self._embedded_lists.append(
                {"id": eid, "repo": repo, "tw": tw, "container": container}
            )
            self._active_list = len(self._embedded_lists) - 1

            # Focus the first edit field with error handling
            try:
                first_task_widget = tw.findChild(QTextEdit)
                if first_task_widget and not first_task_widget.isDeleted():
                    QTimer.singleShot(
                        10, lambda: self._safe_focus_widget(first_task_widget)
                    )
            except Exception:
                pass

            self.embedded_changed.emit()
            self.changed.emit()
        except Exception as e:
            print(f"Error in add_task_list: {e}")
            import traceback

            traceback.print_exc()

    def _safe_focus_widget(self, widget):
        """Safely focus a widget with error handling."""
        try:
            if widget and not widget.isDeleted() and widget.isVisible():
                widget.setFocus()
        except Exception:
            pass

    def _on_embedded_task_changed(self):
        self.embedded_changed.emit()
        self.changed.emit()

    def _remove_embedded_list(self, container):
        for i, el in enumerate(self._embedded_lists):
            if el["container"] is container:
                self._embedded_layout.removeWidget(container)
                container.setParent(None)
                container.deleteLater()
                self._embedded_lists.pop(i)
                if self._active_list is not None:
                    if self._active_list >= len(self._embedded_lists):
                        self._active_list = len(self._embedded_lists) - 1
                self.embedded_changed.emit()
                self.changed.emit()
                return

    def _add_task_to_active_list(self):
        if self._active_list is not None and self._active_list < len(
            self._embedded_lists
        ):
            self._embedded_lists[self._active_list]["tw"]._add_task()

    def set_active_list_from_widget(self, widget):
        try:
            for i, el in enumerate(self._embedded_lists):
                if el["container"] is widget or el["tw"] is widget:
                    self._active_list = i
                    return
        except Exception:
            pass

    def to_serialized_content(self):
        try:
            if not self.editor or self.editor.isDeleted():
                return ""
            if not self._embedded_lists:
                return self.editor.toHtml()
            task_lists = []
            for el in self._embedded_lists:
                tasks = el["repo"].get_by_block(el["id"])
                task_lists.append(
                    [
                        {
                            "text": t.text,
                            "is_checked": t.is_checked,
                            "recurrence_type": t.recurrence_type,
                            "due_date": t.due_date,
                        }
                        for t in tasks
                    ]
                )
            return json.dumps(
                {
                    "text": self.editor.toHtml(),
                    "task_lists": task_lists,
                }
            )
        except Exception as e:
            print(f"Error in to_serialized_content: {e}")
            return ""

    def _switch_to_edit(self):
        if self.editing:
            return
        self.editing = True
        self._text_stack.setCurrentWidget(self.editor)
        self.editor.setFocus()
        self.editor.moveCursor(QTextCursor.MoveOperation.End)
        self.editing_changed.emit(True)

    def _on_focus_lost(self):
        """Switch to preview only if focus moved to a non-block widget."""
        focused = QApplication.focusWidget()
        if isinstance(focused, QToolButton | QPushButton | QComboBox | QLabel):
            return
        if focused is not None and type(focused).__name__ in (
            "ResizeHandle",
            "ResizeHandleHeader",
            "DragHandle",
            "ContentBlockWidget",
        ):
            return
        self._switch_to_preview()

    def _switch_to_preview(self):
        if not self.editing:
            return
        self.editing = False
        self._text_stack.setCurrentWidget(self.preview)
        self._update_preview()
        self.editing_changed.emit(False)

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
        try:
            self.changed.emit()
            self._update_preview()
        except Exception as e:
            print(f"Error in text changed: {e}")

    def _update_preview(self):
        try:
            if not self.editor:
                return
            html = self.editor.toHtml()
            if self.preview:
                font = self.editor.document().defaultFont()
                current_families = list(font.families())
                if "Segoe UI Emoji" not in current_families:
                    current_families.insert(0, "Segoe UI Emoji")
                    font.setFamilies(current_families)
                self.preview.document().setDefaultFont(font)
                self.preview.setHtml(html)
        except Exception as e:
            print(f"Error updating preview: {e}")

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

    def apply_rich_format(self, fmt_name):
        self._switch_to_edit()
        _apply_format_to_edit(self.editor, fmt_name)

    def toPlainText(self):
        return self.editor.toPlainText()


class TableCell(QWidget):
    textChanged = pyqtSignal()

    def __init__(self, text="", row=0, col=0, table_widget=None, parent=None):
        super().__init__(parent)
        self._table_row = row
        self._table_col = col
        self._table = table_widget
        self._task_widget = None
        self._task_repo = None
        self._task_block_id = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._edit = FormattedTextEdit()
        self._edit.setAcceptRichText(True)
        if text and text.strip().startswith("<") and ">" in text.strip():
            self._edit.setHtml(text)
        else:
            self._edit.setPlainText(text)
        self._edit.setMinimumHeight(40)
        self._edit.setMaximumHeight(120)
        self._edit.textChanged.connect(self.textChanged.emit)
        self._edit.setFrameShape(QFrame.Shape.NoFrame)
        self._edit.installEventFilter(self)
        layout.addWidget(self._edit)

        self.setFocusProxy(self._edit)

    def _set_selected(self, selected: bool):
        try:
            if not hasattr(self, "_edit") or not self._edit:
                return
            if selected:
                self._edit.setStyleSheet(
                    "QTextEdit { border: 2px solid #CFA6D6;"
                    " border-radius: 8px; background: #FFFBFD; }"
                )
            else:
                self._edit.setStyleSheet("")
        except Exception as e:
            print(f"Error in _set_selected: {e}")

    def eventFilter(self, obj, event):
        try:
            if obj is self._edit:
                if event.type() == QEvent.Type.KeyPress:
                    if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                        return False  # Let normal text editing handle delete
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def toPlainText(self):
        try:
            if self._task_widget:
                return self._serialize_tasks()
            return _get_edit_html_body(self._edit)
        except Exception as e:
            print(f"Error in toPlainText: {e}")
            import traceback

            traceback.print_exc()
            return ""

    def setPlainText(self, text):
        if self._task_widget:
            self._remove_task_widget()
        if text and text.strip().startswith("<") and ">" in text.strip():
            self._edit.setHtml(text)
        else:
            self._edit.setPlainText(text)

    def textCursor(self):
        return self._edit.textCursor()

    def setCurrentCharFormat(self, fmt):
        self._edit.setCurrentCharFormat(fmt)

    def font(self):
        return self._edit.font()

    def setAcceptRichText(self, val):
        pass

    def setMaximumHeight(self, h):
        self._edit.setMaximumHeight(h)

    def minimumHeight(self):
        return self._edit.minimumHeight()

    def hasFocus(self):
        return self._edit.hasFocus() or (
            self._task_widget and self._task_widget.hasFocus()
        )

    def setFocus(self, reason=...):
        if self._task_widget:
            self._task_widget.setFocus()
        else:
            self._edit.setFocus()

    def setFixedHeight(self, h):
        self._edit.setFixedHeight(h)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Tab:
            if self._table and hasattr(self._table, "_focus_next_cell"):
                try:
                    self._table._focus_next_cell(self._table_row, self._table_col)
                except Exception:
                    pass
            event.accept()
        elif event.key() == Qt.Key.Key_Backtab:
            if self._table and hasattr(self._table, "_focus_prev_cell"):
                try:
                    self._table._focus_prev_cell(self._table_row, self._table_col)
                except Exception:
                    pass
            event.accept()
        else:
            super().keyPressEvent(event)

    def add_task_list(self):
        try:
            if self._task_widget:
                return
            self._task_block_id -= 1
            from src.repositories.in_memory_task_repo import InMemoryTaskRepo

            self._task_repo = InMemoryTaskRepo()
            from src.models.task import Task

            task = Task(content_block_id=self._task_block_id, text="New task")
            self._task_repo.create(task)
            self._task_widget = TaskWidget(
                self._task_block_id, parent=self, task_repo=self._task_repo
            )
            self._task_widget.task_changed.connect(self._on_tasks_changed)
            self.layout().addWidget(self._task_widget)
            if self._table:
                try:
                    self._table.rows[self._table_row][self._table_col] = (
                        self.toPlainText()
                    )
                    self._table._mark_dirty()
                    self._table.tasks_changed.emit()
                except Exception:
                    pass
            self._notify_block_widget()
        except Exception as e:
            print(f"Error in TableCell.add_task_list: {e}")
            import traceback

            traceback.print_exc()

    def _remove_task_widget(self):
        try:
            if self._task_widget:
                self._task_widget.setParent(None)
                self._task_widget.deleteLater()
                self._task_widget = None
                self._task_repo = None
                self._edit.setVisible(True)
                if self._table:
                    self._table.rows[self._table_row][self._table_col] = (
                        self._edit.toPlainText()
                    )
        except Exception as e:
            print(f"Error in _remove_task_widget: {e}")
            import traceback

            traceback.print_exc()

    def _notify_block_widget(self):
        try:
            current = self.parent()
            while current:
                if isinstance(current, ContentBlockWidget):
                    current._on_table_cell_activated(self)
                    return
                try:
                    current = current.parent()
                except Exception:
                    break
        except Exception as e:
            print(f"Error in _notify_block_widget: {e}")
            import traceback

            traceback.print_exc()

    def _serialize_tasks(self):
        try:
            if not self._task_repo:
                return self._edit.toPlainText()
            tasks = self._task_repo.get_by_block(self._task_block_id)
            return json.dumps(
                {
                    "_type": "tasks",
                    "tasks": [
                        {
                            "text": t.text,
                            "is_checked": t.is_checked,
                            "recurrence_type": t.recurrence_type,
                            "due_date": t.due_date,
                        }
                        for t in tasks
                    ],
                }
            )
        except Exception as e:
            print(f"Error in _serialize_tasks: {e}")
            import traceback

            traceback.print_exc()
            return ""

    def _on_tasks_changed(self):
        try:
            self.textChanged.emit()
            if self._table:
                self._table.tasks_changed.emit()
                self._table.rows[self._table_row][self._table_col] = self.toPlainText()
        except Exception as e:
            print(f"Error in _on_tasks_changed: {e}")
            import traceback

            traceback.print_exc()

    @staticmethod
    def from_task_data(tasks_data, row=0, col=0, table_widget=None):
        cell = TableCell.__new__(TableCell)
        cell.__init__("", row=row, col=col, table_widget=table_widget)
        cell._task_block_id -= 1
        from src.repositories.in_memory_task_repo import InMemoryTaskRepo

        cell._task_repo = InMemoryTaskRepo()
        for td in tasks_data:
            from src.models.task import Task

            task = Task(
                content_block_id=cell._task_block_id,
                text=td.get("text", ""),
                is_checked=td.get("is_checked", False),
                recurrence_type=td.get("recurrence_type", "none"),
                due_date=td.get("due_date"),
            )
            cell._task_repo.create(task)
        cell._task_widget = TaskWidget(
            cell._task_block_id, parent=cell, task_repo=cell._task_repo
        )
        cell._task_widget.task_changed.connect(cell._on_tasks_changed)
        cell.layout().addWidget(cell._task_widget)
        if cell._table:
            cell._table.rows[cell._table_row][cell._table_col] = cell.toPlainText()
        cell._notify_block_widget()
        return cell


class TableHeaderCell(QTextEdit):
    def __init__(self, text="", col=0, table_widget=None, parent=None):
        super().__init__(parent)
        self._col = col
        self._table = table_widget
        self.setPlainText(text)
        self.setAcceptRichText(True)
        self.setMinimumHeight(36)
        self.setMaximumHeight(120)
        self.setFrameShape(QFrame.Shape.NoFrame)
        font = self.document().defaultFont()
        font.setBold(True)
        self.document().setDefaultFont(font)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            "QTextEdit { background: #FFF5F7; border: 1px solid #F0E6E8;"
            " border-radius: 8px; font-weight: bold; color: #2E2B2B; }"
        )
        self.textChanged.connect(self._on_changed)

    def _on_changed(self):
        if self._table:
            self._table._mark_dirty()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Tab:
            if self._table:
                self._table._focus_next_header_cell(self._col)
            event.accept()
        elif event.key() == Qt.Key.Key_Backtab:
            if self._table:
                self._table._focus_prev_header_cell(self._col)
            event.accept()
        else:
            super().keyPressEvent(event)


class RowNumCell(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(30)
        self.setFixedWidth(40)
        self.setStyleSheet(
            "QLabel { background: #FFF5F7; border: 1px solid #F0E6E8;"
            " border-radius: 8px; font-weight: bold; color: #CFA6D6;"
            " font-size: 11px; padding: 2px; }"
        )


class TableWidget(QWidget):
    changed = pyqtSignal()
    tasks_changed = pyqtSignal()

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
        self._headers = []
        self._show_row_numbers = False
        self._selected_cells: set[tuple[int, int]] = set()
        self._selection_anchor: tuple[int, int] | None = None
        self._parse_content(content)
        self._btn_header.setChecked(bool(self._headers))
        self._btn_header.setText("- Header" if self._headers else "+ Header")
        self._btn_row_nums.setChecked(self._show_row_numbers)
        self._btn_row_nums.setText("- Row #" if self._show_row_numbers else "+ Row #")
        self._rebuild()

    def _build_toolbar(self, parent):
        bar = QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)
        btn_style = (
            "QPushButton { font-size: 11px; padding: 4px 10px;"
            " border: none; border-radius: 14px;"
            " background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            " stop:0 #FFFFFF, stop:1 #FFF8F5); color: #2E2B2B; }"
            " QPushButton:hover {"
            " background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            " stop:0 #FFF0F3, stop:1 #F7D1DC);"
            " border: 1px solid #F7D1DC; }"
            " QPushButton:pressed { background: #F7D1DC;"
            " border: 1px solid #CFA6D6; }"
            " QPushButton:checked {"
            " background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            " stop:0 #F3E8F6, stop:1 #E8DDE0);"
            " border: 1px solid #CFA6D6; }"
        )
        btn_add_row = QPushButton("+ Row")
        btn_add_row.setStyleSheet(btn_style)
        btn_del_row = QPushButton("- Row")
        btn_del_row.setStyleSheet(btn_style)
        btn_add_col = QPushButton("+ Col")
        btn_add_col.setStyleSheet(btn_style)
        btn_del_col = QPushButton("- Col")
        btn_del_col.setStyleSheet(btn_style)
        self._btn_header = QPushButton("+ Header")
        self._btn_header.setStyleSheet(btn_style)
        self._btn_header.setCheckable(True)
        self._btn_row_nums = QPushButton("+ Row #")
        self._btn_row_nums.setStyleSheet(btn_style)
        self._btn_row_nums.setCheckable(True)
        btn_add_row.clicked.connect(self._add_row)
        btn_del_row.clicked.connect(self._delete_last_row)
        btn_add_col.clicked.connect(self._add_col)
        btn_del_col.clicked.connect(self._delete_last_col)
        self._btn_header.clicked.connect(self._toggle_header)
        self._btn_row_nums.clicked.connect(self._toggle_row_numbers)
        bar.addWidget(btn_add_row)
        bar.addWidget(btn_del_row)
        bar.addWidget(btn_add_col)
        bar.addWidget(btn_del_col)
        bar.addSpacing(8)
        bar.addWidget(self._btn_header)
        bar.addWidget(self._btn_row_nums)
        bar.addStretch()
        parent.addLayout(bar)

    def _parse_content(self, content):
        self.rows.clear()
        self._headers = []
        self._show_row_numbers = False
        lines = content.strip().split("\n")
        for line in lines:
            if line.startswith("{") and (
                '"headers"' in line or '"row_numbers"' in line
            ):
                try:
                    data = json.loads(line)
                    if isinstance(data, dict):
                        if "headers" in data:
                            self._headers = data["headers"]
                        if "row_numbers" in data:
                            self._show_row_numbers = data["row_numbers"]
                    continue
                except (json.JSONDecodeError, TypeError):
                    pass
            if line.startswith("|") and line.endswith("|"):
                cells = [c.strip() for c in line.strip("|").split("|")]
                self.rows.append(cells)
        if not self.rows:
            cols = len(self._headers) if self._headers else 2
            self.rows = [[""] * cols]

    def _rebuild(self):
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w:
                w.setParent(None)

        col_offset = 1 if self._show_row_numbers else 0
        row_offset = 0

        if self._headers:
            if self._show_row_numbers:
                hdr_cell = RowNumCell("#")
                self.grid.addWidget(hdr_cell, 0, 0)
            for c, hval in enumerate(self._headers):
                hcell = TableHeaderCell(hval, col=c + col_offset, table_widget=self)
                self.grid.addWidget(hcell, 0, c + col_offset)
            row_offset = 1

        for r, row in enumerate(self.rows):
            if self._show_row_numbers:
                num_cell = RowNumCell(str(r + 1))
                self.grid.addWidget(num_cell, r + row_offset, 0)
            for c, val in enumerate(row):
                cell = self._create_cell(val, r, c)
                cell.textChanged.connect(self._mark_dirty)
                self.grid.addWidget(cell, r + row_offset, c + col_offset)

    def _create_cell(self, val, r, c):
        if isinstance(val, str) and val.startswith("{") and val.endswith("}"):
            try:
                data = json.loads(val)
                if isinstance(data, dict) and data.get("_type") == "tasks":
                    return TableCell.from_task_data(
                        data.get("tasks", []), row=r, col=c, table_widget=self
                    )
            except (json.JSONDecodeError, TypeError):
                pass
        return TableCell(val, row=r, col=c, table_widget=self)

    def _toggle_header(self, checked):
        if checked:
            cols = len(self.rows[0]) if self.rows else 2
            self._headers = [f"Column {i + 1}" for i in range(cols)]
            self._btn_header.setText("- Header")
        else:
            self._headers = []
            self._btn_header.setText("+ Header")
        self._rebuild()
        self._mark_dirty()

    def _toggle_row_numbers(self, checked):
        self._show_row_numbers = checked
        self._btn_row_nums.setText("- Row #" if checked else "+ Row #")
        self._rebuild()
        self._mark_dirty()

    def _add_row(self):
        cols = len(self.rows[0]) if self.rows else 2
        self.rows.append([""] * cols)
        self._rebuild()
        self._mark_dirty()

    def _delete_last_row(self):
        if len(self.rows) > (0 if self._headers else 1):
            self.rows.pop()
            self._rebuild()
            self._mark_dirty()

    def _add_col(self):
        if self._headers:
            self._headers.append(f"Column {len(self._headers) + 1}")
        for row in self.rows:
            row.append("")
        self._rebuild()
        self._mark_dirty()

    def _delete_last_col(self):
        if self._headers and len(self._headers) > 1:
            self._headers.pop()
        if len(self.rows[0]) > 1:
            for row in self.rows:
                row.pop()
            self._rebuild()
            self._mark_dirty()
        elif self._headers and not self.rows[0]:
            self._rebuild()
            self._mark_dirty()

    def _mark_dirty(self):
        self.changed.emit()

    def _cell_clicked(self, row, col, ctrl=False, shift=False):
        """Handle cell click for multi-selection."""
        try:
            if ctrl:
                # Toggle selection
                cell = (row, col)
                if cell in self._selected_cells:
                    self._selected_cells.discard(cell)
                else:
                    self._selected_cells.add(cell)
                self._selection_anchor = cell
            elif shift and self._selection_anchor:
                # Range selection
                anchor_row, anchor_col = self._selection_anchor
                self._selected_cells.clear()
                min_row = min(anchor_row, row)
                max_row = max(anchor_row, row)
                min_col = min(anchor_col, col)
                max_col = max(anchor_col, col)
                for r in range(min_row, max_row + 1):
                    for c in range(min_col, max_col + 1):
                        self._selected_cells.add((r, c))
            else:
                # Single selection
                self._selected_cells.clear()
                self._selected_cells.add((row, col))
                self._selection_anchor = (row, col)

            # Update visual selection
            self._update_cell_selection_visual()
        except Exception as e:
            print(f"Error in _cell_clicked: {e}")
            import traceback

            traceback.print_exc()

    def _update_cell_selection_visual(self):
        """Update visual state of all cells based on selection."""
        try:
            col_offset = 1 if self._show_row_numbers else 0
            row_offset = 1 if self._headers else 0

            for r, row in enumerate(self.rows):
                for c, _val in enumerate(row):
                    try:
                        w = self.grid.itemAtPosition(r + row_offset, c + col_offset)
                        if w and w.widget() and isinstance(w.widget(), TableCell):
                            cell = w.widget()
                            is_selected = (r, c) in self._selected_cells
                            cell._set_selected(is_selected)
                    except Exception as e:
                        print(f"Error updating cell {r},{c} selection: {e}")
        except Exception as e:
            print(f"Error in _update_cell_selection_visual: {e}")
            import traceback

            traceback.print_exc()

    def _delete_selected_cells(self):
        """Clear content of all selected cells."""
        try:
            if not self._selected_cells:
                return

            col_offset = 1 if self._show_row_numbers else 0
            row_offset = 1 if self._headers else 0

            for row, col in self._selected_cells:
                w = self.grid.itemAtPosition(row + row_offset, col + col_offset)
                if w and w.widget() and isinstance(w.widget(), TableCell):
                    cell = w.widget()
                    cell._edit.clear()

            self._mark_dirty()
        except Exception as e:
            print(f"Error in _delete_selected_cells: {e}")
            import traceback

            traceback.print_exc()

    def _clear_selection(self):
        """Clear all cell selections."""
        try:
            self._selected_cells.clear()
            self._selection_anchor = None
            self._update_cell_selection_visual()
        except Exception as e:
            print(f"Error in _clear_selection: {e}")

    def _focus_next_header_cell(self, c):
        col_offset = 1 if self._show_row_numbers else 0
        if c < len(self._headers) - 1 + col_offset:
            w = self.grid.itemAtPosition(0, c + 1)
            if w and w.widget():
                w.widget().setFocus()
        elif self.rows:
            w = self.grid.itemAtPosition(1, col_offset)
            if w and w.widget():
                w.widget().setFocus()

    def _focus_prev_header_cell(self, c):
        col_offset = 1 if self._show_row_numbers else 0
        if c > col_offset:
            w = self.grid.itemAtPosition(0, c - 1)
            if w and w.widget():
                w.widget().setFocus()

    def to_markdown(self):
        lines = []
        if self._headers or self._show_row_numbers:
            meta = {}
            if self._headers:
                meta["headers"] = self._headers
            if self._show_row_numbers:
                meta["row_numbers"] = True
            lines.append(json.dumps(meta))
        for r, row in enumerate(self.rows):
            cells = []
            for c in range(len(row)):
                w = self.grid.itemAtPosition(
                    r + (1 if self._headers else 0),
                    c + (1 if self._show_row_numbers else 0),
                )
                text = w.widget().toPlainText() if w and w.widget() else ""
                cells.append(text)
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines)

    def _focus_next_cell(self, r, c):
        col_offset = 1 if self._show_row_numbers else 0
        row_offset = 1 if self._headers else 0
        if r == len(self.rows) - 1 and c == len(self.rows[0]) - 1:
            self._add_row()
            r = len(self.rows) - 1
            c = 0
        elif c < len(self.rows[0]) - 1:
            c += 1
        else:
            r += 1
            c = 0
        w = self.grid.itemAtPosition(r + row_offset, c + col_offset)
        if w and w.widget():
            w.widget().setFocus()

    def _focus_prev_cell(self, r, c):
        col_offset = 1 if self._show_row_numbers else 0
        row_offset = 1 if self._headers else 0
        if c > 0:
            c -= 1
        elif r > 0:
            r -= 1
            c = len(self.rows[0]) - 1
        else:
            return
        w = self.grid.itemAtPosition(r + row_offset, c + col_offset)
        if w and w.widget():
            w.widget().setFocus()

    def save_content(self):
        BlockRepo().update(
            ContentBlock(id=self.block_id, content_markdown=self.to_markdown())
        )


class _TaskRowResizeHandle(QWidget):
    def __init__(self, row_widget):
        super().__init__()
        self._row_widget = row_widget
        self.setFixedHeight(4)
        self.setCursor(Qt.CursorShape.SplitVCursor)
        self._dragging = False
        self._start_y = 0
        self._start_h = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_y = event.globalPosition().y()
            self._start_h = self._row_widget.height()

    def mouseMoveEvent(self, event):
        if self._dragging:
            dy = event.globalPosition().y() - self._start_y
            new_h = max(30, int(self._start_h + dy))
            self._row_widget.setFixedHeight(new_h)

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def paintEvent(self, event):
        p = QPainter(self)
        r = self.rect()
        p.fillRect(r, QColor("#e8e8e8"))
        # Subtle center line
        y = r.height() // 2
        p.setPen(QColor("#cccccc"))
        p.drawLine(r.left() + 10, y, r.right() - 10, y)


class _TaskRowSplitHandle(QWidget):
    """Drag handle between the QTextEdit and sidebar.

    Resizes only the edit width.
    """

    def __init__(self, edit_widget):
        super().__init__()
        self._edit = edit_widget
        self.setFixedWidth(8)
        self.setCursor(Qt.CursorShape.SplitHCursor)
        self._dragging = False
        self._start_x = 0
        self._start_edit_w = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_x = event.globalPosition().x()
            self._start_edit_w = self._edit.width()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging:
            dx = event.globalPosition().x() - self._start_x
            new_w = max(100, int(self._start_edit_w + dx))
            pw = self.parent().width()
            available = pw - self.width()
            self._edit.setFixedWidth(min(new_w, available))

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def paintEvent(self, event):
        p = QPainter(self)
        r = self.rect()
        p.fillRect(r, QColor("#eef0f4"))
        x = r.width() // 2
        p.setPen(QColor("#bbbfc8"))
        p.drawLine(x, r.top() + 3, x, r.bottom() - 3)


class TaskWidget(QWidget):
    task_changed = pyqtSignal()

    def __init__(self, block_id, content="", parent=None, task_repo=None):
        super().__init__(parent)
        self.block_id = block_id
        from src.repositories.task_repo import TaskRepo

        self.task_repo = task_repo if task_repo is not None else TaskRepo()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._load()

    def _clear(self):
        layout = self.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                sub = item.layout()
                while sub.count():
                    sub_item = sub.takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()

    def _load(self):
        self._clear()
        layout = self.layout()

        tasks = self.task_repo.get_by_block(self.block_id)

        for task in tasks:
            container = QWidget()
            v_layout = QVBoxLayout(container)
            v_layout.setContentsMargins(0, 0, 0, 0)
            v_layout.setSpacing(0)

            # Top row
            h_layout = QHBoxLayout()
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(0)

            cb = QCheckBox()
            cb.setChecked(bool(task.is_checked))
            cb.stateChanged.connect(lambda state, t=task: self._toggle_task(t, state))
            h_layout.addWidget(cb)

            edit = FormattedTextEdit()
            edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            edit.setFrameShape(QFrame.Shape.NoFrame)
            edit.setAcceptRichText(True)
            edit.setMinimumHeight(26)
            edit.blockSignals(True)
            task_text = task.text or ""
            if task_text.strip().startswith("<") and ">" in task_text.strip():
                edit.setHtml(task_text)
            else:
                edit.setPlainText(task_text)
            edit.blockSignals(False)
            edit.textChanged.connect(
                lambda t=task, e=edit, c=container: (
                    self._update_text(t, _get_edit_html_body(e)),
                    self._auto_grow_edit(e, c),
                )
            )

            # edit_container stretches; inside: edit at left,
            # split handle, stretch pushes them left
            edit_container = QWidget()
            edit_inner = QHBoxLayout(edit_container)
            edit_inner.setContentsMargins(0, 0, 0, 0)
            edit_inner.setSpacing(0)
            edit_inner.addWidget(edit)
            split_handle = _TaskRowSplitHandle(edit)
            edit_inner.addWidget(split_handle)
            edit_inner.addStretch(1)

            h_layout.addWidget(edit_container, 1)

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

            # Sidebar stays at right edge of the outer row
            sidebar = QWidget()
            side_inner = QHBoxLayout(sidebar)
            side_inner.setContentsMargins(0, 0, 0, 0)
            side_inner.setSpacing(0)
            side_inner.addWidget(QLabel("Recur:"))
            side_inner.addWidget(rec_combo)
            side_inner.addWidget(del_btn)

            h_layout.addWidget(sidebar)

            v_layout.addLayout(h_layout)

            height_handle = _TaskRowResizeHandle(container)
            v_layout.addWidget(height_handle)

            # Start at single-line height; auto-grow after layout resolves
            container.setFixedHeight(30)
            QTimer.singleShot(0, lambda c=container, e=edit: self._auto_grow_edit(e, c))

            layout.addWidget(container)

    def _auto_grow_edit(self, edit, container):
        doc_h = edit.document().size().height()
        ideal_edit_h = max(26, int(doc_h) + 4)
        ideal_container_h = ideal_edit_h + 6
        if ideal_container_h > container.height():
            container.setFixedHeight(ideal_container_h)

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

        undo_manager.push(
            {
                "type": "task",
                "task": _task_dict(task),
            }
        )
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
        self.setFixedHeight(8)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self._hovered = False
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
        w = self.width()
        if self._hovered or self._dragging:
            p.fillRect(self.rect(), QColor("#e0e7ff"))
        p.setPen(QColor("#d1d5db"))
        cx = w // 2
        for i in range(3):
            p.drawLine(
                cx - 8 + i * 5, self.height() // 2, cx - 4 + i * 5, self.height() // 2
            )

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        if not self._dragging:
            self._hovered = False
        self._in_corner = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_y = event.globalPosition().toPoint().y()
            self._start_x = event.globalPosition().toPoint().x()
            self._start_height = self.block_widget.height()
            self._start_width = self.block_widget.width()
            self._in_corner = self._is_in_corner(event.position().toPoint().x())
            self.block_widget._manual_resize = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._dragging:
            try:
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
                    self.block_widget.setFixedWidth(new_w)
                    self.block_widget.setMinimumHeight(new_h)
                    self.block_widget.resize(self.block_widget.width(), new_h)
                if isinstance(self.block_widget._body, MarkdownBlock):
                    editor_h = max(30, new_h - 60)
                    self.block_widget._body.editor.setMinimumHeight(editor_h)
                    self.block_widget._body.preview.setMinimumHeight(editor_h)
                elif isinstance(self.block_widget._body, TableWidget):
                    data_rows = len(self.block_widget._body.rows)
                    total_rows = data_rows + (
                        1 if self.block_widget._body._headers else 0
                    )
                    for i in range(self.block_widget._body.grid.count()):
                        it = self.block_widget._body.grid.itemAt(i)
                        if it and it.widget():
                            if isinstance(it.widget(), TableCell):
                                cell_h = max(30, (new_h - 80) // max(1, data_rows))
                                it.widget().setMaximumHeight(cell_h + 20)
                            elif isinstance(it.widget(), TableHeaderCell | RowNumCell):
                                hdr_h = max(36, (new_h - 80) // max(1, total_rows))
                                it.widget().setFixedHeight(hdr_h + 10)
            except Exception as e:
                print(f"Error during resize: {e}")
        else:
            in_corner = self._is_in_corner(event.position().toPoint().x())
            if in_corner != self._in_corner:
                self._in_corner = in_corner
                self.setCursor(
                    Qt.CursorShape.SizeFDiagCursor
                    if in_corner
                    else Qt.CursorShape.SizeVerCursor
                )

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._hovered = True
        self.update()
        try:
            if hasattr(self.block_widget, "mark_dirty"):
                self.block_widget.mark_dirty()
        except Exception as e:
            print(f"Error marking dirty after resize: {e}")


class ResizeHandleHeader(QWidget):
    def __init__(self, header_container, edit_widget, parent=None):
        super().__init__(parent)
        self._header_container = header_container
        self._edit_widget = edit_widget
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
            p.drawLine(cx - 6, y, cx + 6, y)

    def enterEvent(self, event):
        self.setStyleSheet(
            "background: #e0e7ff; border-top: 1px solid #6366f1;"
            " border-bottom: 1px solid #6366f1;"
        )

    def leaveEvent(self, event):
        if not self._dragging:
            self.setStyleSheet("background: transparent;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_y = event.globalPosition().toPoint().y()
            self._start_h = self._header_container.height()
            self.setStyleSheet("background: #6366f1;")
            block_w = self._header_container.parent()
            while block_w and not isinstance(block_w, ContentBlockWidget):
                block_w = block_w.parent()
            if block_w:
                block_w._manual_resize = True

    def mouseMoveEvent(self, event):
        if self._dragging:
            delta = event.globalPosition().toPoint().y() - self._start_y
            min_h = max(36, self._edit_widget.height())
            new_h = max(min_h, self._start_h + delta)
            self._header_container.setFixedHeight(new_h)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self.setStyleSheet("background: #e0e7ff;")
        block_w = self._header_container.parent()
        while block_w and not isinstance(block_w, ContentBlockWidget):
            block_w = block_w.parent()
        if block_w:
            block_w.mark_dirty()


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
        self._manual_resize = False
        self._active_task_cell = None
        self._dirty = True

        self._build_ui()

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def mark_dirty(self):
        self._dirty = True

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.position().toPoint().x() >= self.width() - 8:
                self._right_resizing = True
                self._right_resize_start_x = event.globalPosition().toPoint().x()
                self._right_resize_start_w = self.width()
                self._manual_resize = True
                event.accept()
                return
            mods = QApplication.keyboardModifiers()
            add_to_selection = mods in (
                Qt.KeyboardModifier.ShiftModifier,
                Qt.KeyboardModifier.ControlModifier,
            )
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
            self.mark_dirty()
            return
        super().mouseReleaseEvent(event)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.drag_handle = DragHandle()

        default_header = (
            self.block.header if self.block.header else self.block.block_type
        )
        header_size = (
            self.block.header_font_size
            if self.block.header_font_size and self.block.header_font_size >= 1
            else 9
        )
        self._pending_header_font_size = None
        self._header_align_h = self.block.header_align_h
        self._header_align_v = self.block.header_align_v

        header_font = QFont("Segoe UI", header_size, QFont.Weight.DemiBold)

        self._header_container = QWidget()
        self._header_container.setObjectName("header_container")
        self._header_v_layout = QVBoxLayout(self._header_container)
        self._header_v_layout.setContentsMargins(0, 0, 0, 0)
        self._header_v_layout.setSpacing(0)

        self._header_edit = QTextEdit()
        self._header_edit.setObjectName("block_header_edit")
        self._header_edit.setPlainText(default_header)
        self._header_edit.setPlaceholderText(self.block.block_type)
        self._header_edit.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._header_edit.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._header_edit.setTabChangesFocus(True)
        self._header_edit.setFont(header_font)
        self._header_edit.setFrameShape(QFrame.Shape.NoFrame)
        self._header_edit.document().setDocumentMargin(1)
        self._header_edit.setFixedHeight(max(30, int(header_size * 1.6 + 8)))
        self._header_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        _orig_header_focus = self._header_edit.focusInEvent

        def _on_header_focus(ev, orig=_orig_header_focus, me=self):
            orig(ev)
            me.header_focused.emit(me)
            QTimer.singleShot(0, me._apply_pending_header_font)

        self._header_edit.focusInEvent = _on_header_focus
        _orig_header_focus_out = self._header_edit.focusOutEvent

        def _on_header_focus_out(ev, orig=_orig_header_focus_out, me=self):
            orig(ev)
            if hasattr(me, "_inline_toolbar") and not me._body.editing:
                me._inline_toolbar.setVisible(False)

        self._header_edit.focusOutEvent = _on_header_focus_out
        _orig_header_key = self._header_edit.keyPressEvent

        def _header_key(ev, orig=_orig_header_key, me=self):
            if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                ev.accept()
                me._header_edit.clearFocus()
            else:
                orig(ev)

        self._header_edit.keyPressEvent = _header_key
        self._header_edit.setStyleSheet(
            "QTextEdit { border: none; background: transparent; color: #2E2B2B; }"
            "QTextEdit:focus { border: none; background: #f3f4f6; color: #2E2B2B; }"
        )
        self._header_edit.textChanged.connect(self.mark_dirty)
        self.changed.connect(self.mark_dirty)

        self._apply_v_alignment_layout()

        h_align_map = {
            "left": Qt.AlignmentFlag.AlignLeft,
            "center": Qt.AlignmentFlag.AlignCenter,
            "right": Qt.AlignmentFlag.AlignRight,
        }
        self._header_edit.setAlignment(
            h_align_map.get(self._header_align_h, Qt.AlignmentFlag.AlignLeft)
        )

        container_h = self.block.header_height or max(36, int(header_size * 1.6 + 12))
        self._header_container.setFixedHeight(container_h)

        self._align_target_kind = "header"
        self._align_target_edit = self._header_edit

        icons_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "assets", "icons"
        )

        _tip = (
            " QToolTip { background-color: #FFFFFF; color: #2E2B2B;"
            " border: 1px solid #F0E6E8; border-radius: 8px;"
            " padding: 6px 10px; font-size: 12px; }"
        )

        self._h_align_group = QButtonGroup(self)
        self._h_left_btn = QPushButton()
        self._h_left_btn.setIcon(QIcon(os.path.join(icons_dir, "align_left.svg")))
        self._h_left_btn.setToolTip("Align left")
        self._h_center_btn = QPushButton()
        self._h_center_btn.setIcon(QIcon(os.path.join(icons_dir, "align_center.svg")))
        self._h_center_btn.setToolTip("Align center")
        self._h_right_btn = QPushButton()
        self._h_right_btn.setIcon(QIcon(os.path.join(icons_dir, "align_right.svg")))
        self._h_right_btn.setToolTip("Align right")
        for b in (self._h_left_btn, self._h_center_btn, self._h_right_btn):
            b.setCheckable(True)
            b.setFixedHeight(container_h)
            b.setFixedWidth(32)
            b.setIconSize(QSize(18, 18))
            b.setStyleSheet(
                "QPushButton { padding: 0px; min-height: 0px;"
                " border: 1px solid #e5e7eb; border-radius: 4px; }"
                " QPushButton:checked { background: #f3e8f6;"
                " border-color: #CFA6D6; }"
                " QPushButton:hover { background: #fef2f2; }" + _tip
            )
            self._h_align_group.addButton(b)
        self._h_align_group.buttonClicked.connect(self._on_h_align_changed)

        self._v_align_group = QButtonGroup(self)
        self._v_top_btn = QPushButton()
        self._v_top_btn.setIcon(QIcon(os.path.join(icons_dir, "align_top.svg")))
        self._v_top_btn.setToolTip("Align top")
        self._v_center_btn = QPushButton()
        self._v_center_btn.setIcon(QIcon(os.path.join(icons_dir, "align_middle.svg")))
        self._v_center_btn.setToolTip("Align middle")
        self._v_bottom_btn = QPushButton()
        self._v_bottom_btn.setIcon(QIcon(os.path.join(icons_dir, "align_bottom.svg")))
        self._v_bottom_btn.setToolTip("Align bottom")
        for b in (self._v_top_btn, self._v_center_btn, self._v_bottom_btn):
            b.setCheckable(True)
            b.setFixedHeight(container_h)
            b.setFixedWidth(32)
            b.setIconSize(QSize(18, 18))
            b.setStyleSheet(
                "QPushButton { padding: 0px; min-height: 0px;"
                " border: 1px solid #e5e7eb; border-radius: 4px; }"
                " QPushButton:checked { background: #f3e8f6;"
                " border-color: #CFA6D6; }"
                " QPushButton:hover { background: #fef2f2; }" + _tip
            )
            self._v_align_group.addButton(b)
        self._v_align_group.buttonClicked.connect(self._on_v_align_changed)

        self._apply_alignment_button_states()

        self._dots_btn = QPushButton("⋮")
        self._dots_btn.setFixedHeight(container_h)
        self._dots_btn.setFixedWidth(28)
        self._dots_btn.setToolTip("Alignment & options")
        self._dots_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._dots_btn.setStyleSheet(
            "QPushButton { border: 1px solid #e5e7eb;"
            " border-radius: 4px; color: #9ca3af; font-size: 16px;"
            " font-weight: bold; padding: 0px; }"
            " QPushButton:hover { background: #F3E8F6;"
            " border-color: #CFA6D6; }" + _tip
        )
        self._dots_btn.clicked.connect(self._show_alignment_menu)

        del_btn = QPushButton("✕")
        del_btn.setFixedHeight(container_h)
        del_btn.setToolTip("Delete block")
        del_btn.setStyleSheet(
            "QPushButton { border: 1px solid #e5e7eb;"
            " border-radius: 4px; color: #9ca3af; font-size: 14px;"
            " padding: 0px; min-width: 24px; max-width: 24px; }"
            " QPushButton:hover { color: #ef4444;"
            " border-color: #ef4444; background: #fef2f2; }" + _tip
        )

        header.addWidget(self.drag_handle)
        header.addWidget(self._header_container, 1)
        header.addWidget(self._dots_btn)
        self._add_task_btn = QPushButton("+ Add Task")
        self._add_task_btn.setFixedHeight(container_h)
        self._add_task_btn.setStyleSheet(
            "QPushButton { padding: 0px; min-height: 0px;"
            " border: 1px solid #e5e7eb; border-radius: 4px;"
            " color: #9ca3af; font-size: 11px; }"
            " QPushButton:hover { background: #fef2f2; }" + _tip
        )
        self._add_task_btn.setVisible(False)
        header.addWidget(self._add_task_btn)

        self._fun_imports_btn = QPushButton()
        self._fun_imports_btn.setIcon(QIcon(os.path.join(icons_dir, "folder_fun.svg")))
        self._fun_imports_btn.setFixedSize(container_h, container_h)
        self._fun_imports_btn.setToolTip("Fun Imports (Emoji & GIF)")
        self._fun_imports_btn.setIconSize(QSize(18, 18))
        self._fun_imports_btn.setStyleSheet(
            "QPushButton { padding: 0px; min-height: 0px;"
            " border: 1px solid #e5e7eb; border-radius: 4px; }"
            " QPushButton:hover { background: #F3E8F6;"
            " border-color: #CFA6D6; }" + _tip
        )
        self._fun_imports_btn.clicked.connect(self._open_fun_imports)
        header.addWidget(self._fun_imports_btn)

        header.addWidget(del_btn)

        layout.addLayout(header)

        self._header_resize_handle = ResizeHandleHeader(
            self._header_container, self._header_edit
        )
        layout.addWidget(self._header_resize_handle)

        self._body = None

        if self.block.block_type == "text":
            content_size = (
                self.block.content_font_size
                if self.block.content_font_size and self.block.content_font_size >= 1
                else 13
            )
            self._body = MarkdownBlock(
                self.block.id,
                self.block.content_markdown,
                content_font_size=content_size,
            )
            self._body.changed.connect(self._on_content_changed)
            self._body.embedded_changed.connect(self._fit_to_content)
            self._body.embedded_changed.connect(self._sync_add_task_btn)
            self._build_inline_toolbar(layout)
            self._inline_toolbar.setVisible(False)
            self._body.editing_changed.connect(self._on_editing_changed)
            self.header_focused.connect(self._on_header_focus_changed)
            layout.addWidget(self._body)
            self._body.editor.focused.connect(
                lambda ed=self: self.content_focused.emit(ed)
            )
            self._add_task_btn.clicked.connect(self._body._add_task_to_active_list)
            QTimer.singleShot(0, self._sync_add_task_btn)
        elif self.block.block_type == "table":
            self._body = TableWidget(self.block.id, self.block.content_markdown)
            self._body.changed.connect(self._on_content_changed)
            self._body.tasks_changed.connect(self._fit_to_content)
            layout.addWidget(self._body)
            self._add_task_btn.clicked.connect(self._add_task_to_active_cell)
        elif self.block.block_type in ("list", "checkbox"):
            self._body = TaskWidget(self.block.id, self.block.content_markdown)
            self._body.task_changed.connect(self._on_content_changed)
            self._add_task_btn.setVisible(True)
            self._add_task_btn.clicked.connect(self._body._add_task)
            self._body_scroll = QScrollArea()
            self._body_scroll.setWidget(self._body)
            self._body_scroll.setWidgetResizable(True)
            self._body_scroll.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self._body_scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self._body_scroll.setFrameShape(QFrame.Shape.NoFrame)
            layout.addWidget(self._body_scroll)
            if self.block.height:
                QTimer.singleShot(0, self._fit_to_content)

        self.resize_handle = ResizeHandle(self)
        layout.addWidget(self.resize_handle)

        if self.block.height:
            self._apply_height(self.block.height)
        else:
            self._apply_height(200)

        if self.block.width:
            self.setFixedWidth(self.block.width)
        else:
            QTimer.singleShot(0, self._set_initial_width)

        del_btn.clicked.connect(self._delete)

    def _apply_height(self, h):
        h = max(80, h)
        try:
            if isinstance(self._body, MarkdownBlock):
                inner_h = max(30, h - 64)
                self._body.editor.setMinimumHeight(inner_h)
                self._body.preview.setMinimumHeight(inner_h)
            elif isinstance(self._body, TableWidget):
                data_rows = len(self._body.rows)
                total_rows = data_rows + (1 if self._body._headers else 0)
                for i in range(self._body.grid.count()):
                    w = self._body.grid.itemAt(i)
                    if w and w.widget():
                        if isinstance(w.widget(), TableCell):
                            cell_h = max(30, (h - 64) // max(1, data_rows))
                            w.widget().setMaximumHeight(cell_h)
                        elif isinstance(w.widget(), TableHeaderCell | RowNumCell):
                            w.widget().setFixedHeight(
                                max(36, (h - 64) // max(1, total_rows))
                            )
            elif isinstance(self._body, TaskWidget):
                inner_h = max(30, h - 64)
                self._body_scroll.setMinimumHeight(inner_h)
        except Exception as e:
            print(f"Error in _apply_height: {e}")
        self.setMinimumHeight(h)
        self.resize(self.width(), h)

    def _set_initial_width(self):
        p = self.parent()
        if p:
            self.setFixedWidth(int(p.width() / 3))

    def _sync_add_task_btn(self):
        if isinstance(self._body, MarkdownBlock) and self._body._embedded_lists:
            self._add_task_btn.setVisible(True)
        elif isinstance(self._body, MarkdownBlock):
            self._add_task_btn.setVisible(False)

    def _add_task_to_active_cell(self):
        try:
            if self._active_task_cell and self._active_task_cell._task_widget:
                self._active_task_cell._task_widget._add_task()
        except Exception as e:
            print(f"Error in _add_task_to_active_cell: {e}")
            import traceback

            traceback.print_exc()

    def _on_table_cell_activated(self, cell):
        try:
            self._active_task_cell = cell
            if hasattr(self, "_add_task_btn") and self._add_task_btn:
                if cell and cell._task_widget:
                    self._add_task_btn.setVisible(True)
                else:
                    self._add_task_btn.setVisible(False)
        except Exception as e:
            print(f"Error in _on_table_cell_activated: {e}")
            import traceback

            traceback.print_exc()

    def _on_content_changed(self):
        self.changed.emit()
        if isinstance(self._body, TaskWidget):
            self._fit_to_content()

    def _on_editing_changed(self, editing):
        if hasattr(self, "_inline_toolbar"):
            self._inline_toolbar.setVisible(editing)
        if hasattr(self, "_dots_btn"):
            self._dots_btn.setVisible(editing)
        if hasattr(self, "_fun_imports_btn"):
            self._fun_imports_btn.setVisible(editing)
        if not editing and hasattr(self, "_header_edit"):
            self._saved_header_align = self._header_edit.alignment()
            self._header_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif (
            editing
            and hasattr(self, "_header_edit")
            and hasattr(self, "_saved_header_align")
        ):
            self._header_edit.setAlignment(self._saved_header_align)

    def _on_header_focus_changed(self, block_w):
        if block_w is self:
            if hasattr(self, "_inline_toolbar"):
                self._inline_toolbar.setVisible(True)
            if hasattr(self, "_dots_btn"):
                self._dots_btn.setVisible(True)
            if hasattr(self, "_fun_imports_btn"):
                self._fun_imports_btn.setVisible(True)

    def _fit_to_content(self):
        if self._manual_resize:
            return
        self.setMinimumHeight(0)
        if isinstance(self._body, TaskWidget):
            hh = 0
            for i in range(self._body.layout().count()):
                item = self._body.layout().itemAt(i)
                if item.widget():
                    hh += item.widget().height()
                elif item.layout():
                    max_row = 0
                    for j in range(item.layout().count()):
                        sub = item.layout().itemAt(j)
                        if sub.widget():
                            max_row = max(max_row, sub.widget().sizeHint().height())
                    hh += max_row
            spacing = self._body.layout().spacing()
            num_items = self._body.layout().count()
            hh += spacing * (num_items - 1) if num_items > 1 else 0
            margins = self.layout().contentsMargins()
            layout_spacing = self.layout().spacing()
            header_h = self._header_container.height()
            handle_h = self.resize_handle.height()
            padding = margins.top() + margins.bottom() + layout_spacing * 2 + 16
            h = max(60, hh + header_h + handle_h + padding)
        else:
            self.layout().activate()
            h = max(60, self.layout().sizeHint().height() + 20)
        if h <= self.height():
            return
        self.setMinimumHeight(h)
        self.resize(self.width(), h)
        self.block.height = h

    def _delete(self):
        from src.undo_manager import _block_dict, _task_dict

        tasks_data = [_task_dict(t) for t in TaskRepo().get_by_block(self.block.id)]
        undo_manager.push(
            {
                "type": "block",
                "block": _block_dict(self.block),
                "tasks": tasks_data,
            }
        )
        BlockRepo().delete(self.block.id)
        self.delete_requested.emit(self)

    def _open_fun_imports(self):
        from src.ui.sidebar import FunImportsDialog

        target_edit = None

        focused = QApplication.focusWidget()

        if focused is self._header_edit:
            target_edit = self._header_edit
        elif isinstance(self._body, MarkdownBlock):
            if not self._body.editing:
                self._body._switch_to_edit()
            target_edit = self._body.editor
        elif isinstance(self._body, TableWidget):
            if self._active_task_cell and hasattr(self._active_task_cell, "_edit"):
                target_edit = self._active_task_cell._edit
            elif focused and isinstance(focused, FormattedTextEdit):
                target_edit = focused
        elif isinstance(self._body, TaskWidget):
            if focused and isinstance(focused, FormattedTextEdit):
                target_edit = focused

        dialog = FunImportsDialog(None, target_edit=target_edit)
        self._fun_imports_btn.setDown(False)
        self._fun_imports_btn.setChecked(False)
        dialog.exec()
        self._fun_imports_btn.setAttribute(Qt.WidgetAttribute.WA_UnderMouse, False)
        self._fun_imports_btn.update()

    def _show_alignment_menu(self):
        """Show alignment dropdown menu from the ⋮ button."""
        icons_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "assets", "icons"
        )
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #ffffff; border: 1px solid #e5e7eb;
                border-radius: 8px; padding: 4px; }
            QMenu::item { padding: 6px 24px; border-radius: 4px;
                font-size: 12px; color: #374151; }
            QMenu::item:selected { background: #F3E8F6; }
            QMenu::separator { height: 1px; background: #e5e7eb; margin: 4px 8px; }
        """)

        h_group = QActionGroup(self)
        h_group.setExclusive(True)
        h_left = QAction("Align Left", self)
        h_left.setIcon(QIcon(os.path.join(icons_dir, "align_left.svg")))
        h_center = QAction("Align Center", self)
        h_center.setIcon(QIcon(os.path.join(icons_dir, "align_center.svg")))
        h_right = QAction("Align Right", self)
        h_right.setIcon(QIcon(os.path.join(icons_dir, "align_right.svg")))
        for a in (h_left, h_center, h_right):
            h_group.addAction(a)
            menu.addAction(a)
        h_map = {"left": h_left, "center": h_center, "right": h_right}
        checked = h_map.get(self._header_align_h, h_left)
        checked.setChecked(True)

        menu.addSeparator()

        v_group = QActionGroup(self)
        v_group.setExclusive(True)
        v_top = QAction("Align Top", self)
        v_top.setIcon(QIcon(os.path.join(icons_dir, "align_top.svg")))
        v_center = QAction("Align Middle", self)
        v_center.setIcon(QIcon(os.path.join(icons_dir, "align_middle.svg")))
        v_bottom = QAction("Align Bottom", self)
        v_bottom.setIcon(QIcon(os.path.join(icons_dir, "align_bottom.svg")))
        for a in (v_top, v_center, v_bottom):
            v_group.addAction(a)
            menu.addAction(a)
        v_map = {"top": v_top, "center": v_center, "bottom": v_bottom}
        checked_v = v_map.get(self._header_align_v, v_top)
        checked_v.setChecked(True)

        def on_h_align(action):
            if action == h_left:
                self._header_align_h = "left"
            elif action == h_center:
                self._header_align_h = "center"
            elif action == h_right:
                self._header_align_h = "right"
            h_align_map = {
                "left": Qt.AlignmentFlag.AlignLeft,
                "center": Qt.AlignmentFlag.AlignCenter,
                "right": Qt.AlignmentFlag.AlignRight,
            }
            self._header_edit.setAlignment(
                h_align_map.get(self._header_align_h, Qt.AlignmentFlag.AlignLeft)
            )
            self._apply_alignment_button_states()
            self.mark_dirty()

        def on_v_align(action):
            if action == v_top:
                self._header_align_v = "top"
            elif action == v_center:
                self._header_align_v = "center"
            elif action == v_bottom:
                self._header_align_v = "bottom"
            self._apply_v_alignment_layout()
            self._apply_alignment_button_states()
            self.mark_dirty()

        h_group.triggered.connect(on_h_align)
        v_group.triggered.connect(on_v_align)

        menu.exec(self._dots_btn.mapToGlobal(self._dots_btn.rect().bottomLeft()))

    def _build_inline_toolbar(self, parent_layout):
        """Build inline formatting toolbar for text blocks."""
        self._inline_toolbar = QWidget()
        self._inline_toolbar.setStyleSheet("background: transparent;")
        tb_layout = QHBoxLayout(self._inline_toolbar)
        tb_layout.setContentsMargins(4, 4, 4, 4)
        tb_layout.setSpacing(2)

        _tip_style = (
            " QToolTip { background-color: #FFFFFF; color: #2E2B2B;"
            " border: 1px solid #F0E6E8; border-radius: 8px;"
            " padding: 6px 10px; font-size: 12px; }"
        )
        tb_style = (
            "QToolButton { font-size: 13px; border: 1px solid transparent;"
            " border-radius: 6px; padding: 3px 8px; color: #6B6770;"
            " min-width: 24px; }"
            " QToolButton:hover { background: #FFF0F3;"
            " border-color: #F7D1DC; color: #2E2B2B; }"
            " QToolButton:checked { background: #F3E8F6;"
            " border-color: #CFA6D6; color: #2E2B2B; }" + _tip_style
        )

        self._in_bold_btn = QToolButton()
        self._in_bold_btn.setText("B")
        self._in_bold_btn.setCheckable(True)
        self._in_bold_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._in_bold_btn.setToolTip("Bold (Ctrl+B)")
        self._in_bold_btn.setStyleSheet(
            "QToolButton { font-weight: bold; font-size: 14px;"
            " border: 1px solid transparent; border-radius: 6px;"
            " padding: 3px 8px; color: #6B6770; min-width: 24px; }"
            " QToolButton:hover { background: #FFF0F3;"
            " border-color: #F7D1DC; color: #2E2B2B; }"
            " QToolButton:checked { background: #F3E8F6;"
            " border-color: #CFA6D6; color: #2E2B2B; }" + _tip_style
        )

        self._in_italic_btn = QToolButton()
        self._in_italic_btn.setText("I")
        self._in_italic_btn.setCheckable(True)
        self._in_italic_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._in_italic_btn.setToolTip("Italic (Ctrl+I)")
        self._in_italic_btn.setStyleSheet(
            "QToolButton { font-style: italic; font-size: 14px;"
            " border: 1px solid transparent; border-radius: 6px;"
            " padding: 3px 8px; color: #6B6770; min-width: 24px; }"
            " QToolButton:hover { background: #FFF0F3;"
            " border-color: #F7D1DC; color: #2E2B2B; }"
            " QToolButton:checked { background: #F3E8F6;"
            " border-color: #CFA6D6; color: #2E2B2B; }" + _tip_style
        )

        sep1 = QLabel("│")
        sep1.setStyleSheet("color: #e5e7eb; padding: 0 2px; font-size: 12px;")

        self._in_h1_btn = QToolButton()
        self._in_h1_btn.setText("H1")
        self._in_h1_btn.setCheckable(True)
        self._in_h1_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._in_h1_btn.setToolTip("Heading 1")
        self._in_h1_btn.setStyleSheet(tb_style)

        self._in_h2_btn = QToolButton()
        self._in_h2_btn.setText("H2")
        self._in_h2_btn.setCheckable(True)
        self._in_h2_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._in_h2_btn.setToolTip("Heading 2")
        self._in_h2_btn.setStyleSheet(tb_style)

        self._in_code_btn = QToolButton()
        self._in_code_btn.setText("<>")
        self._in_code_btn.setCheckable(True)
        self._in_code_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._in_code_btn.setToolTip("Code")
        self._in_code_btn.setStyleSheet(tb_style)

        sep2 = QLabel("│")
        sep2.setStyleSheet("color: #e5e7eb; padding: 0 2px; font-size: 12px;")

        self._in_link_btn = QToolButton()
        self._in_link_btn.setText("🔗")
        self._in_link_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._in_link_btn.setToolTip("Insert Link")
        self._in_link_btn.setStyleSheet(tb_style)

        self._in_bullet_btn = QToolButton()
        self._in_bullet_btn.setText("•")
        self._in_bullet_btn.setCheckable(True)
        self._in_bullet_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._in_bullet_btn.setToolTip("Bullet List")
        self._in_bullet_btn.setStyleSheet(tb_style)

        sep3 = QLabel("│")
        sep3.setStyleSheet("color: #e5e7eb; padding: 0 2px; font-size: 12px;")

        size_label = QLabel("Size:")
        size_label.setStyleSheet("color: #6B6770; font-size: 11px; padding: 0 2px;")
        self._in_font_size_combo = QComboBox()
        self._in_font_size_combo.addItems(
            [str(s) for s in [9, 10, 11, 12, 13, 14, 15, 16, 18, 20, 22, 24, 28, 32]]
        )
        initial_size = (
            self.block.content_font_size
            if self.block.content_font_size and self.block.content_font_size >= 1
            else 13
        )
        self._in_font_size_combo.setCurrentText(str(initial_size))
        self._in_font_size_combo.setFixedWidth(36)
        self._in_font_size_combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._in_font_size_combo.setToolTip("Font size")
        self._in_font_size_combo.setStyleSheet(
            "QComboBox { font-size: 11px; padding: 2px 2px;"
            " border: 1px solid #e5e7eb; border-radius: 4px;"
            " background: #fff; }"
            " QComboBox::drop-down { border: none; width: 12px; }"
            " QComboBox QAbstractItemView { font-size: 11px; }" + _tip_style
        )

        for w in (
            self._in_bold_btn,
            self._in_italic_btn,
            sep1,
            self._in_h1_btn,
            self._in_h2_btn,
            self._in_code_btn,
            sep2,
            self._in_link_btn,
            self._in_bullet_btn,
            sep3,
            size_label,
            self._in_font_size_combo,
        ):
            tb_layout.addWidget(w)
        tb_layout.addStretch()

        parent_layout.addWidget(self._inline_toolbar)

        self._in_bold_btn.clicked.connect(lambda: self._inline_format("bold"))
        self._in_italic_btn.clicked.connect(lambda: self._inline_format("italic"))
        self._in_h1_btn.clicked.connect(lambda: self._inline_format("h1"))
        self._in_h2_btn.clicked.connect(lambda: self._inline_format("h2"))
        self._in_code_btn.clicked.connect(lambda: self._inline_format("code"))
        self._in_link_btn.clicked.connect(lambda: self._inline_format("link"))
        self._in_bullet_btn.clicked.connect(lambda: self._inline_format("bullet"))
        self._in_font_size_combo.currentTextChanged.connect(
            self._on_inline_font_size_changed
        )

    def _inline_format(self, fmt):
        """Apply formatting from the inline toolbar to this block's editor."""
        if not isinstance(self._body, MarkdownBlock):
            return
        edit = self._body.editor
        if not self._body.editing:
            self._body._switch_to_edit()
        try:
            _apply_format_to_edit(edit, fmt, self)
        except Exception as e:
            print(f"Error in inline format: {e}")

    def _on_inline_font_size_changed(self, text):
        """Handle font size change from inline toolbar."""
        if not isinstance(self._body, MarkdownBlock):
            return
        try:
            size = int(text)
        except ValueError:
            return
        edit = self._body.editor
        if not self._body.editing:
            self._body._switch_to_edit()
        cursor = edit.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            fmt.setFontPointSize(size)
            cursor.mergeCharFormat(fmt)
        else:
            fmt = QTextCharFormat()
            fmt.setFontPointSize(size)
            edit.setCurrentCharFormat(fmt)
        self.block.content_font_size = size
        self.mark_dirty()

    def _apply_pending_header_font(self):
        if self._pending_header_font_size:
            fmt = QTextCharFormat()
            fmt.setFontPointSize(self._pending_header_font_size)
            self._header_edit.setCurrentCharFormat(fmt)
            self._pending_header_font_size = None

    def _set_header_height_from_size(self, size):
        single = max(30, int(size * 1.6 + 8))
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
        h_map = {
            "left": self._h_left_btn,
            "center": self._h_center_btn,
            "right": self._h_right_btn,
        }
        v_map = {
            "top": self._v_top_btn,
            "center": self._v_center_btn,
            "bottom": self._v_bottom_btn,
        }
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
            v_map = {
                "top": self._v_top_btn,
                "center": self._v_center_btn,
                "bottom": self._v_bottom_btn,
            }
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
            self.mark_dirty()

    def _on_v_align_changed(self, btn):
        if btn == self._v_top_btn:
            self._header_align_v = "top"
        elif btn == self._v_center_btn:
            self._header_align_v = "center"
        elif btn == self._v_bottom_btn:
            self._header_align_v = "bottom"
        self._apply_v_alignment_layout()
        self.mark_dirty()

    def save(self):
        try:
            self.block.pos_x = self.x()
            self.block.pos_y = self.y()
            self.block.height = (
                self.minimumHeight() if self.minimumHeight() > 0 else None
            )
            if self.minimumWidth() > 0 and self.minimumWidth() == self.maximumWidth():
                self.block.width = self.minimumWidth()
            else:
                self.block.width = None
            text = self._header_edit.toPlainText().strip()
            self.block.header = text if text and text != self.block.block_type else None
            cursor = self._header_edit.textCursor()
            pt = cursor.charFormat().fontPointSize()
            self.block.header_font_size = (
                int(pt) if pt >= 1 else self._header_edit.font().pointSize()
            )
            self.block.header_align_h = self._header_align_h
            self.block.header_align_v = self._header_align_v
            self.block.header_height = self._header_container.height()
            if self._body and isinstance(self._body, MarkdownBlock):
                self.block.content_font_size = self._body.content_font_size
            if self.block.block_type == "table" and self._body:
                self.block.content_markdown = self._body.to_markdown()
            elif self.block.block_type == "text" and self._body:
                self.block.content_markdown = self._body.to_serialized_content()
            BlockRepo().update(self.block)
            self._dirty = False
            self.saved.emit()
        except Exception as e:
            print(f"Error saving block: {e}")


class Canvas(QWidget):
    clicked_at = pyqtSignal(int, int)
    image_pasted = pyqtSignal(object)

    _bg_pixmap: QPixmap | None = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
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


class PageEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page_id = None
        self.block_repo = BlockRepo()
        self._block_widgets: list[ContentBlockWidget] = []
        self._selected_block_widgets: set[ContentBlockWidget] = set()
        self._font_target: tuple[ContentBlockWidget, str] | None = None
        self._active_text_body = None
        self._active_table_cell = None
        self._tracked_edit: QTextEdit | None = None
        self._syncing_buttons = False  # Prevent re-entrant calls
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

        # Add welcome message
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

        main_layout.addWidget(self.scroll, 1)

        self._drag_data = (
            None  # (widget, start_x, start_y, start_mouse_x, start_mouse_y)
        )
        self._canvas_click_pos: tuple[int, int] | None = None

        QApplication.instance().focusChanged.connect(self._on_focus_changed)

    def _center_welcome_label(self):
        """Center the welcome label in the canvas."""
        if hasattr(self, "welcome_label") and self.welcome_label.isVisible():
            canvas_width = self.content.width()
            canvas_height = self.content.height()
            label_width = self.welcome_label.width()
            label_height = self.welcome_label.height()
            x = (canvas_width - label_width) // 2
            y = (canvas_height - label_height) // 10  # Position slightly above center
            self.welcome_label.move(x, y)

    def eventFilter(self, obj, event):
        if obj is self.scroll.viewport() and event.type() == QEvent.Type.Resize:
            if self.current_page_id is None:
                # Welcome screen: fit canvas to viewport
                vp = self.scroll.viewport()
                self.content.setFixedWidth(vp.width())
                self.content.resize(vp.width(), vp.height())
            else:
                self._update_canvas_size()
            self._center_welcome_label()
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

        btn_style = (
            "QPushButton { padding: 6px 16px; border: none;"
            " border-radius: 20px;"
            " background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            " stop:0 #FFFFFF, stop:1 #FFF8F5);"
            " font-size: 12px; font-weight: 500; color: #2E2B2B; }"
            " QPushButton:hover {"
            " background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            " stop:0 #FFF0F3, stop:1 #F7D1DC);"
            " border: 1px solid #F7D1DC; }"
            " QPushButton:pressed { background: #F7D1DC;"
            " border: 1px solid #CFA6D6; }"
        )
        self._add_block_btn = QPushButton("+ Text")
        self._add_block_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._add_block_btn.setStyleSheet(btn_style)
        self._table_btn = QPushButton("+ Table")
        self._table_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table_btn.setStyleSheet(btn_style)
        self._list_btn = QPushButton("+ List")
        self._list_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list_btn.setStyleSheet(btn_style)
        self._template_btn = QPushButton("Template")
        self._template_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._template_btn.setStyleSheet(btn_style)

        for b in [
            self._add_block_btn,
            self._table_btn,
            self._list_btn,
            self._template_btn,
        ]:
            toolbar.addWidget(b)

        parent_layout.addWidget(toolbar_widget)

        self._add_block_btn.clicked.connect(lambda: self._add_block("text"))
        self._table_btn.clicked.connect(lambda: self._add_block("table"))
        self._list_btn.clicked.connect(self._on_add_list)
        self._template_btn.clicked.connect(self._insert_template)

    @staticmethod
    def _find_block_widget(widget):
        try:
            current = widget
            while current:
                if isinstance(current, ContentBlockWidget):
                    return current
                try:
                    current = current.parent()
                except Exception:
                    break
        except Exception:
            pass
        return None

    @staticmethod
    def _find_nearest_table_cell(widget):
        try:
            current = widget
            while current:
                if isinstance(current, TableCell):
                    return current
                try:
                    current = current.parent()
                except Exception:
                    break
        except Exception:
            pass
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
            line = getattr(block_w, "_active_line", None)
            if line:
                size = line.font().pointSize() if line else 13
            else:
                focus_widget = QApplication.focusWidget()
                if isinstance(focus_widget, QTextEdit):
                    cursor = focus_widget.textCursor()
                    pt = cursor.charFormat().fontPointSize()
                    fw_size = focus_widget.font().pointSize()
                    size = int(pt) if pt >= 1 else (fw_size if fw_size >= 1 else 13)
                else:
                    size = 13
        elif part == "table_cell":
            cell = getattr(block_w, "_active_cell", None)
            if cell:
                cursor = cell.textCursor()
                pt = cursor.charFormat().fontPointSize()
                cell_size = cell.font().pointSize()
                size = int(pt) if pt >= 1 else (cell_size if cell_size >= 1 else 13)
            else:
                size = 13
        else:
            try:
                size = block_w._body.content_font_size
            except AttributeError:
                return
        if hasattr(block_w, "_in_font_size_combo") and block_w._in_font_size_combo:
            block_w._in_font_size_combo.blockSignals(True)
            block_w._in_font_size_combo.setCurrentText(str(size))
            block_w._in_font_size_combo.blockSignals(False)

    def _on_block_header_focused(self, block_w):
        self._font_target = (block_w, "header")
        self._set_font_combo_from_target()

    def _on_block_content_focused(self, block_w):
        self._font_target = (block_w, "content")
        self._set_font_combo_from_target()

    def _is_in_table_cell(self, widget):
        """Safely check if a widget is inside a TableCell without segfault."""
        try:
            p = widget.parent()
            return isinstance(p, TableCell)
        except Exception:
            return False

    def _on_focus_changed(self, old, new):
        if new is None:
            for bw in self._block_widgets:
                if (
                    hasattr(bw, "_body")
                    and hasattr(bw._body, "editing")
                    and bw._body.editing
                ):
                    bw._body._switch_to_preview()
            return
        # Track table cell / text body focus IMMEDIATELY so _on_add_list can use it
        try:
            if new and isinstance(new, FormattedTextEdit):
                try:
                    p = new.parent()
                    if isinstance(p, TableCell):
                        self._active_table_cell = p
                        self._active_text_body = None
                except Exception:
                    pass
                return  # Skip deferred processing for table cells
            elif new and isinstance(new, MarkdownTextEdit | QTextBrowser):
                try:
                    block_w = self._find_block_widget(new)
                    if (
                        block_w
                        and hasattr(block_w, "_body")
                        and isinstance(block_w._body, MarkdownBlock)
                    ):
                        self._active_text_body = block_w._body
                        self._active_table_cell = None
                except Exception:
                    pass
                return  # Skip deferred processing for text blocks
        except Exception:
            pass

        # Skip ALL deferred processing for buttons, combos, labels, etc.
        # Only process focus changes for actual content widgets
        if new and isinstance(
            new, QToolButton | QComboBox | QPushButton | QLabel | QSpinBox | QDateEdit
        ):
            return

        # Defer processing only for content widgets (text edits, headers, etc.)
        try:
            QTimer.singleShot(0, lambda n=new: self._process_focus_change(n))
        except Exception:
            pass

    def _process_focus_change(self, new):
        try:
            if not new:
                return
            try:
                if isinstance(new, RowNumCell):
                    return
            except Exception:
                return

            try:
                block_w = self._find_block_widget(new)
            except Exception:
                return
            if not block_w:
                self._sync_format_buttons()
                return

            new_type = type(new).__name__

            if (
                new_type == "QTextEdit"
                and hasattr(new, "objectName")
                and new.objectName() == "block_header_edit"
            ):
                self._font_target = (block_w, "header")
                self._set_font_combo_from_target()
                if hasattr(block_w, "_set_align_target"):
                    block_w._set_align_target("header", block_w._header_edit)
            elif (
                new_type == "QLineEdit"
                and hasattr(block_w, "_body")
                and isinstance(block_w._body, TaskWidget)
            ):
                block_w._active_line = new
                self._font_target = (block_w, "list_item")
                self._set_font_combo_from_target()
            elif (
                new_type == "QTextEdit"
                and hasattr(block_w, "_body")
                and isinstance(block_w._body, TaskWidget)
            ):
                self._font_target = (block_w, "list_item")
                self._set_font_combo_from_target()
            elif new_type in ("MarkdownTextEdit", "QTextBrowser"):
                try:
                    self._font_target = (block_w, "content")
                    self._set_font_combo_from_target()
                except AttributeError:
                    pass
                if hasattr(block_w, "_set_align_target") and hasattr(block_w, "_body"):
                    try:
                        block_w._set_align_target("content", block_w._body.editor)
                    except Exception:
                        pass
            elif (
                new_type == "QTextEdit"
                and hasattr(block_w, "_body")
                and isinstance(block_w._body, MarkdownBlock)
            ):
                try:
                    p = new.parent()
                    while p:
                        if isinstance(p, _EmbeddedTaskContainer):
                            block_w._body.set_active_list_from_widget(p)
                            break
                        p = p.parent()
                except Exception:
                    pass

            QTimer.singleShot(0, self._sync_format_buttons)
        except Exception as e:
            print(f"Error in _process_focus_change: {e}")
            import traceback

            traceback.print_exc()

    def _connect_cursor_tracking(self):
        # No longer connecting cursorPositionChanged to avoid crashes on Enter/typing
        pass

    def _get_active_text_edit(self):
        try:
            focus_widget = QApplication.focusWidget()
            if focus_widget:
                if isinstance(focus_widget, MarkdownTextEdit):
                    for w in self._block_widgets:
                        try:
                            if hasattr(w, "_body") and isinstance(
                                w._body, MarkdownBlock
                            ):
                                if w._body.editor.hasFocus():
                                    return w._body.editor, w
                        except RuntimeError:
                            continue
                elif isinstance(focus_widget, QTextEdit):
                    block_w = self._find_block_widget(focus_widget)
                    if block_w:
                        if self._is_in_table_cell(focus_widget):
                            return focus_widget, block_w
                        if hasattr(block_w, "_body") and isinstance(
                            block_w._body, TaskWidget
                        ):
                            return focus_widget, block_w
                        if hasattr(block_w, "_body") and isinstance(
                            block_w._body, MarkdownBlock
                        ):
                            p = focus_widget.parent()
                            while p:
                                if isinstance(p, _EmbeddedTaskContainer):
                                    return focus_widget, block_w
                                p = p.parent()
                        if hasattr(block_w, "_body") and isinstance(
                            block_w._body, TableWidget
                        ):
                            return focus_widget, block_w
            if self._active_text_body:
                try:
                    if hasattr(self._active_text_body, "editor"):
                        return self._active_text_body.editor, self._find_block_widget(
                            self._active_text_body
                        )
                except RuntimeError:
                    self._active_text_body = None
            if self._active_table_cell:
                try:
                    if hasattr(self._active_table_cell, "_edit"):
                        block_w = self._find_block_widget(self._active_table_cell)
                        return self._active_table_cell._edit, block_w
                except RuntimeError:
                    self._active_table_cell = None
        except Exception:
            pass
        return None, None

    def _sync_format_buttons(self):
        if self._syncing_buttons:
            return

        try:
            self._syncing_buttons = True

            edit, block_w = self._get_active_text_edit()
            if not edit or not block_w:
                return

            # Sync inline toolbar buttons if this is a text block
            if not hasattr(block_w, "_in_bold_btn") or not block_w._in_bold_btn:
                return

            try:
                cursor = edit.textCursor()
            except RuntimeError:
                return
            char_fmt = cursor.charFormat()

            is_bold = char_fmt.fontWeight() >= QFont.Weight.Bold
            is_italic = char_fmt.fontItalic()
            pt_size = char_fmt.fontPointSize()
            if pt_size < 1:
                pt_size = edit.font().pointSize()
            is_h1 = pt_size >= 19 and is_bold
            is_h2 = not is_h1 and pt_size >= 15 and is_bold
            is_code = False

            is_bullet = False
            try:
                block = cursor.block()
                if block.isValid():
                    text_list = block.textList()
                    if text_list:
                        is_bullet = (
                            text_list.format().style() == QTextListFormat.Style.ListDisc
                        )
            except Exception:
                pass

            btns = (
                block_w._in_bold_btn,
                block_w._in_italic_btn,
                block_w._in_h1_btn,
                block_w._in_h2_btn,
                block_w._in_code_btn,
                block_w._in_bullet_btn,
            )
            for btn in btns:
                btn.blockSignals(True)
            block_w._in_bold_btn.setChecked(is_bold)
            block_w._in_italic_btn.setChecked(is_italic)
            block_w._in_h1_btn.setChecked(is_h1)
            block_w._in_h2_btn.setChecked(is_h2)
            block_w._in_code_btn.setChecked(is_code)
            block_w._in_bullet_btn.setChecked(is_bullet)
            for btn in btns:
                btn.blockSignals(False)
        except Exception as e:
            print(f"Error syncing format buttons: {e}")
        finally:
            self._syncing_buttons = False

    def clear_editor(self):
        self.current_page_id = None
        self.page_title.setText("Select a page")
        self._clear_selection()
        self._active_text_body = None
        self._active_table_cell = None
        for w in self._block_widgets:
            w.setParent(None)
            w.deleteLater()
        self._block_widgets.clear()
        # Disable scrolling for welcome screen
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        vp = self.scroll.viewport()
        self.content.setFixedWidth(vp.width())
        self.content.resize(vp.width(), vp.height())
        self.scroll.setStyleSheet("QScrollArea { border: none; background: #2a1a35; }")
        self.content.setPhotoBackground(True)
        # Show welcome message
        self.welcome_label.show()
        self._center_welcome_label()
        self.setStyleSheet("background: #2a1a35;")

    def load_page(self, page_id: int):
        self.current_page_id = page_id
        self._active_text_body = None
        self._active_table_cell = None
        from src.repositories.page_repo import PageRepo

        page = PageRepo().get_by_id(page_id)
        self.page_title.setText(page.title if page else "Untitled")
        self._clear_selection()
        # Hide welcome message and re-enable scrolling
        self.welcome_label.hide()
        self.content.setPhotoBackground(False)
        self.setStyleSheet("background: #FFF8F5;")
        self.scroll.setStyleSheet("QScrollArea { border: none; background: #FFF8F5; }")
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

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
        def _start_drag(ev, w):
            self._drag_data = (
                w,
                w.x(),
                w.y(),
                ev.globalPosition().toPoint().x(),
                ev.globalPosition().toPoint().y(),
            )
            w.raise_()
            ev.accept()

        def _make_move(orig):
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
                    orig(ev)

            return _drag_move

        def _make_release(orig):
            def _drag_release(ev, w=widget):
                if self._drag_data and self._drag_data[0] is w:
                    w.block.pos_x = w.x()
                    w.block.pos_y = w.y()
                    w.mark_dirty()
                    self._drag_data = None
                    ev.accept()
                else:
                    orig(ev)

            return _drag_release

        # Drag handle patching (keep existing)
        orig_handle_press = widget.drag_handle.mousePressEvent

        def _handle_press(ev, w=widget):
            if ev.button() == Qt.MouseButton.LeftButton:
                _start_drag(ev, w)
            else:
                orig_handle_press(ev)

        widget.drag_handle.mousePressEvent = _handle_press
        widget.drag_handle.mouseMoveEvent = _make_move(
            widget.drag_handle.mouseMoveEvent
        )
        widget.drag_handle.mouseReleaseEvent = _make_release(
            widget.drag_handle.mouseReleaseEvent
        )

        # Block widget top-area drag (click on header area → drag entire block)
        orig_block_press = widget.mousePressEvent

        def _block_press(ev, w=widget):
            if ev.button() == Qt.MouseButton.LeftButton:
                x = ev.position().toPoint().x()
                y = ev.position().toPoint().y()
                if x >= w.width() - 8:
                    orig_block_press(ev)
                    return
                top = w._header_container.y() if w._header_container else 0
                bottom = (
                    top + w._header_container.height() if w._header_container else 0
                )
                bottom += (
                    w._header_resize_handle.height() if w._header_resize_handle else 0
                )
                if y <= bottom + 4:
                    _start_drag(ev, w)
                    return
            orig_block_press(ev)

        widget.mousePressEvent = _block_press
        widget.mouseMoveEvent = _make_move(widget.mouseMoveEvent)
        widget.mouseReleaseEvent = _make_release(widget.mouseReleaseEvent)

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
        from src.repositories.task_repo import TaskRepo
        from src.undo_manager import _block_dict, _task_dict

        for w in list(self._selected_block_widgets):
            tasks_data = [_task_dict(t) for t in TaskRepo().get_by_block(w.block.id)]
            undo_manager.push(
                {
                    "type": "block",
                    "block": _block_dict(w.block),
                    "tasks": tasks_data,
                }
            )
            BlockRepo().delete(w.block.id)
        self._clear_selection()
        self.load_page(self.current_page_id)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self._delete_selected_blocks()
            event.accept()
        elif (
            event.key() == Qt.Key.Key_D
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            focus_widget = QApplication.focusWidget()
            if focus_widget and isinstance(focus_widget, QTextEdit | QLineEdit):
                event.ignore()
                return
            self._delete_selected_blocks()
            event.accept()
        elif (
            event.key() == Qt.Key.Key_V
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            focus_widget = QApplication.focusWidget()
            if focus_widget and isinstance(
                focus_widget,
                QTextEdit | QLineEdit | FormattedTextEdit | MarkdownTextEdit,
            ):
                event.ignore()
                return
            clipboard = QApplication.clipboard()
            mime = clipboard.mimeData()
            if mime and mime.hasImage():
                img = mime.imageData()
                if isinstance(img, QImage) and not img.isNull():
                    self._paste_image_to_new_block(img)
                    event.accept()
                    return
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def _paste_image_to_new_block(self, img):
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
                block_type="text",
                pos_x=pos_x,
                pos_y=pos_y,
            )
            self.block_repo.create(block)
            self.load_page(self.current_page_id)
            QTimer.singleShot(0, lambda: self._embed_image_in_last_block(img))
        except Exception:
            traceback.print_exc()

    def _embed_image_in_last_block(self, img):
        if not self._block_widgets:
            return
        last_block = self._block_widgets[-1]
        if hasattr(last_block, "_body") and isinstance(last_block._body, MarkdownBlock):
            edit = last_block._body.editor
            last_block._body._switch_to_edit()
            cursor = edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            doc = edit.document()
            img_name = f"img_{uuid.uuid4().hex}.png"
            doc.addResource(
                QTextDocument.ResourceType.ImageResource, QUrl(img_name), img
            )
            img_fmt = QTextImageFormat()
            max_w = (
                min(img.width(), edit.viewport().width() - 40)
                if edit.viewport().width() > 60
                else img.width()
            )
            if img.width() > max_w:
                ratio = max_w / img.width()
                img_fmt.setWidth(int(max_w))
                img_fmt.setHeight(int(img.height() * ratio))
            else:
                img_fmt.setWidth(img.width())
                img_fmt.setHeight(img.height())
            img_fmt.setName(img_name)
            cursor.insertImage(img_fmt)
            last_block.mark_dirty()
            QTimer.singleShot(0, self._scroll_to_newest_block)

    def _scroll_to_newest_block(self):
        if self._block_widgets:
            self.scroll.ensureWidgetVisible(self._block_widgets[-1], 50, 50)

    def _on_canvas_clicked(self, x, y):
        self._canvas_click_pos = (x, y)
        for bw in self._block_widgets:
            if (
                hasattr(bw, "_body")
                and hasattr(bw._body, "editing")
                and bw._body.editing
            ):
                bw._body._switch_to_preview()

    def _on_add_list(self):
        """Handle +List button click to add embedded task list."""
        # Capture active references immediately before they change
        active_text_body = self._active_text_body
        active_table_cell = self._active_table_cell

        def _do_add():
            try:
                # Try to find table cell or block from focus widget
                focus_widget = QApplication.focusWidget()

                # Check if focus is in a text editing context
                is_in_text_edit = False
                if focus_widget:
                    # Check if focus is in a table cell (safe check)
                    try:
                        table_cell = self._find_nearest_table_cell(focus_widget)
                        if table_cell:
                            try:
                                table_cell.add_task_list()
                            except Exception as e:
                                print(f"Error adding task list to table cell: {e}")
                                import traceback

                                traceback.print_exc()
                            return
                    except Exception:
                        pass

                    # Check if focus is in a markdown block
                    try:
                        block_w = self._find_block_widget(focus_widget)
                        if block_w and hasattr(block_w, "_body"):
                            body = block_w._body
                            if isinstance(body, MarkdownBlock):
                                try:
                                    body.add_task_list()
                                except Exception as e:
                                    print(
                                        f"Error adding task list to markdown block: {e}"
                                    )
                                    import traceback

                                    traceback.print_exc()
                                return
                    except Exception:
                        pass

                    # Check if focus is in any text edit widget
                    is_in_text_edit = isinstance(
                        focus_widget, QTextEdit | FormattedTextEdit | MarkdownTextEdit
                    )

                # If focus is not in a text edit, check fallback references
                # Handles user clicking text box/cell then +List button
                if not is_in_text_edit:
                    # Try table cell first
                    if active_table_cell:
                        try:
                            if active_table_cell.isVisible():
                                try:
                                    active_table_cell.add_task_list()
                                    return
                                except Exception as e:
                                    print(
                                        f"Error adding task list to active table cell: "
                                        f"{e}"
                                    )
                                    import traceback

                                    traceback.print_exc()
                        except Exception:
                            self._active_table_cell = None

                    # Try text body
                    if active_text_body:
                        try:
                            if active_text_body.isVisible():
                                try:
                                    active_text_body.add_task_list()
                                    return
                                except Exception as e:
                                    print(
                                        f"Error adding task list to active text body: "
                                        f"{e}"
                                    )
                                    import traceback

                                    traceback.print_exc()
                        except Exception:
                            self._active_text_body = None
                else:
                    # Focus is in a text edit, use fallback references
                    if active_text_body and active_text_body.isVisible():
                        try:
                            active_text_body.add_task_list()
                            return
                        except Exception:
                            self._active_text_body = None

                    if active_table_cell and active_table_cell.isVisible():
                        try:
                            active_table_cell.add_task_list()
                            return
                        except Exception:
                            self._active_table_cell = None

                # If all else fails, create a new standalone list block
                self._add_block("checkbox")
            except Exception as e:
                print(f"Error in _on_add_list: {e}")
                import traceback

                traceback.print_exc()

        QTimer.singleShot(0, _do_add)

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

        from PyQt6.QtGui import QIcon

        dialog = QDialog(self)
        dialog.setWindowTitle("Insert Template")

        # Title with logo
        title_layout = QHBoxLayout()
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets",
            "icons",
            "logo_icon.svg",
        )
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_label.setPixmap(QIcon(logo_path).pixmap(28, 28))
            title_layout.addWidget(logo_label)
        title_label = QLabel("Insert Template")
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #2E2B2B;"
            " font-family: 'Playfair Display', serif;"
        )
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        layout = QVBoxLayout(dialog)
        layout.addLayout(title_layout)
        list_widget = QListWidget()
        for t in templates:
            list_widget.addItem(f"{t.name} ({t.category})")
        layout.addWidget(list_widget)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if (
            dialog.exec() == QDialog.DialogCode.Accepted
            and list_widget.currentRow() >= 0
        ):
            template = templates[list_widget.currentRow()]
            blocks_data = json.loads(template.content_json)
            for bd in blocks_data:
                block = ContentBlock(
                    page_id=self.current_page_id,
                    block_type=bd.get("block_type", "text"),
                    content_markdown=bd.get("content_markdown", ""),
                )
                self.block_repo.create(block)
            self.load_page(self.current_page_id)

    def save_current(self):
        for w in self._block_widgets:
            if hasattr(w, "save") and hasattr(w, "_dirty") and w._dirty:
                w.save()

        # If this is a template page, update the template in the database
        if self.current_page_id:
            try:
                from src.repositories.block_repo import BlockRepo
                from src.repositories.page_repo import PageRepo
                from src.repositories.template_repo import TemplateRepo

                page = PageRepo().get_by_id(self.current_page_id)
                if page and page.page_type == "template_page":
                    # Get all blocks for this page
                    blocks = BlockRepo().get_by_page(self.current_page_id)
                    data = [
                        {
                            "block_type": b.block_type,
                            "content_markdown": b.content_markdown,
                        }
                        for b in blocks
                    ]

                    # Find and update the corresponding template
                    templates = TemplateRepo().get_all()
                    for template in templates:
                        if template.name == page.title:
                            template.content_json = json.dumps(data)
                            TemplateRepo().update(template)
                            break
            except Exception as e:
                print(f"Error syncing template: {e}")
