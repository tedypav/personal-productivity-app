import json
import os

from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.controllers.editor_controller import EditorController
from src.repositories.page_object_repo import PageObjectRepo
from src.ui.objects.checklist_widget import ChecklistWidget
from src.ui.objects.table_widget import TableWidget
from src.ui.objects.textbox_widget import TextboxWidget


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
        self._textboxes = {}
        self._canvas_click_pos = None
        self._editor_controller = EditorController()
        self.setObjectName("pageEditor")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._build_toolbar(main_layout)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("editorScroll")
        self.scroll.setWidgetResizable(False)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.content = Canvas()
        self.content.clicked_at.connect(self._on_canvas_clicked)
        self.scroll.setWidget(self.content)
        self.scroll.viewport().installEventFilter(self)
        self.scroll.setWidgetResizable(False)
        self.content.setPhotoBackground(True)

        self.welcome_label = QLabel()
        self.welcome_label.setWordWrap(True)
        self.welcome_label.setObjectName("welcome_label")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setTextFormat(Qt.TextFormat.RichText)
        self.welcome_label.setText(
            "Hello, lovely!<br>Let's make it a productive day!"
            ' <span style="font-size:35px;">❤️</span>'
        )
        self.welcome_label.setParent(self.content)
        self.welcome_label.adjustSize()
        self.welcome_label.show()

        self._page_empty_hint = QLabel("Click + buttons to add your first object")
        self._page_empty_hint.setObjectName("editorEmptyHint")
        self._page_empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_empty_hint.setParent(self.content)
        self._page_empty_hint.hide()

        main_layout.addWidget(self.scroll, 1)

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
            vp = self.scroll.viewport()
            self.content.setFixedWidth(vp.width())
            if self.current_page_id is None:
                self.content.resize(vp.width(), vp.height())
            self._center_welcome_label()
            self._center_empty_hint()
        if obj is self.scroll.viewport() and event.type() == QEvent.Type.Wheel:
            sb = self.scroll.verticalScrollBar()
            if sb.value() >= sb.maximum() - 300:
                new_h = self.content.height() + 500
                self.content.resize(self.content.width(), new_h)
        return super().eventFilter(obj, event)

    def _build_toolbar(self, parent_layout):
        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("editorToolbar")

        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(12, 6, 12, 6)

        self.page_title = QLabel("Select a page")
        self.page_title.setObjectName("editorPageTitle")
        toolbar.addWidget(self.page_title)
        toolbar.addStretch()

        self._back_btn = QPushButton("← Back to folder")
        self._back_btn.setObjectName("editorBackBtn")
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.clicked.connect(self._on_back_clicked)
        self._back_btn.hide()
        toolbar.addWidget(self._back_btn)

        self._checkbox_btn = QPushButton("✓ + Checklist")
        self._checkbox_btn.setObjectName("editorChecklistBtn")
        self._checkbox_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checkbox_btn.clicked.connect(self._add_checklist)
        self._checkbox_btn.hide()
        toolbar.addWidget(self._checkbox_btn)

        self._table_btn = QPushButton("⊞ + Table")
        self._table_btn.setObjectName("editorTableBtn")
        self._table_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._table_btn.clicked.connect(self._add_table)
        self._table_btn.hide()
        toolbar.addWidget(self._table_btn)

        self._textbox_btn = QPushButton("T + Text Box")
        self._textbox_btn.setObjectName("editorTextboxBtn")
        self._textbox_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._textbox_btn.clicked.connect(self._add_textbox)
        self._textbox_btn.hide()
        toolbar.addWidget(self._textbox_btn)

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

    def load_page(self, page_id: int):
        from src.repositories.page_repo import PageRepo

        self.current_page_id = page_id
        self.scroll.verticalScrollBar().setValue(0)
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
            self._textbox_btn.hide()
        else:
            self._load_objects()
            self._checkbox_btn.show()
            self._table_btn.show()
            self._textbox_btn.show()
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
        self._group_objects_into_textboxes()

    def _group_objects_into_checklists(self):
        checklists = {}
        for obj in self._objects:
            if obj.object_type in ("checklist_meta", "table_meta", "textbox_meta"):
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
        if not widget._loaded_pos:
            x = (canvas_w - container_w) // 2
            y = 60 + len(self._checklists) * 200 + len(self._tables) * 200
            widget.move(x, y)
        widget.show()
        return widget

    def _group_objects_into_textboxes(self):
        textbox_ids = set()
        for obj in self._objects:
            if obj.object_type == "textbox_meta":
                textbox_id = obj.sort_order // 100
                textbox_ids.add(textbox_id)

        for textbox_id in sorted(textbox_ids):
            self._create_textbox_widget(textbox_id)

    def _create_textbox_widget(self, textbox_id):
        widget = TextboxWidget(
            textbox_id, page_id=self.current_page_id, parent=self.content
        )
        widget.object_delete_requested.connect(self._on_textbox_delete)
        self._textboxes[textbox_id] = widget

        canvas_w = self.content.width()
        container_w = min(500, canvas_w - 80)
        widget.setMinimumWidth(container_w)
        widget._load_meta()
        if not widget._user_width:
            widget._user_width = container_w
        if not widget._loaded_pos:
            x = (canvas_w - container_w) // 2
            y = (
                60
                + len(self._checklists) * 200
                + len(self._tables) * 200
                + len(self._textboxes) * 200
            )
            widget.move(x, y)
        widget.show()
        return widget

    def _add_textbox(self):
        if not self.current_page_id:
            return

        textbox_id = max(self._textboxes.keys(), default=-1) + 1
        widget = self._create_textbox_widget(textbox_id)

        if self._canvas_click_pos:
            x, y = self._canvas_click_pos
            canvas_w = self.content.width()
            container_w = min(500, canvas_w - 80)
            widget.move(max(20, x - container_w // 2), max(60, y - 30))
            self._canvas_click_pos = None

        widget._add_text_block()
        widget._save_meta()
        self._page_empty_hint.hide()

    def _on_textbox_delete(self, textbox_id):
        if textbox_id in self._textboxes:
            widget = self._textboxes[textbox_id]
            widget.exit_all_edit_modes()
            widget.hide()
            widget.deleteLater()
            del self._textboxes[textbox_id]
        meta = PageObjectRepo().get_textbox_meta(self.current_page_id, textbox_id)
        if meta:
            PageObjectRepo().delete(meta.id)
        self._objects = [
            o
            for o in self._objects
            if not (
                o.object_type == "textbox_meta" and o.sort_order // 100 == textbox_id
            )
        ]
        if not self._objects:
            self._page_empty_hint.show()
            self._center_empty_hint()

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
        for widget in self._textboxes.values():
            widget.exit_all_edit_modes()
            widget.hide()
            widget.deleteLater()
        self._textboxes.clear()

    def _show_toc(self, children):
        from PyQt6.QtWidgets import QPushButton

        toc_container = QWidget(self.content)
        toc_container.setObjectName("editorTocContainer")
        toc_layout = QVBoxLayout(toc_container)
        toc_layout.setContentsMargins(40, 40, 40, 40)
        toc_layout.setSpacing(6)

        folder_label = QLabel("Pages in this folder")
        folder_label.setObjectName("editorTocLabel")
        folder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toc_layout.addWidget(folder_label)

        separator = QWidget()
        separator.setObjectName("editorTocSeparator")
        separator.setFixedHeight(1)
        toc_layout.addWidget(separator)
        toc_layout.addSpacing(8)

        for child in children:
            btn = QPushButton(f"  {child.title}")
            btn.setObjectName("editorTocItem")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
        self._textbox_btn.hide()
        self._parent_folder_id = None
        self._canvas_click_pos = None
        self.content.setPhotoBackground(True)
        self._center_welcome_label()
