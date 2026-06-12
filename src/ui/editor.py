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

    def __init__(self, checklist_id, page_id=None, parent=None):
        super().__init__(parent)
        self.checklist_id = checklist_id
        self.page_id = page_id
        self.setObjectName("checklist")
        self.setStyleSheet(
            "#checklist {"
            " background: #FFFFFF; border: 1px solid #F7D1DC;"
            " border-radius: 12px;"
            "}"
        )
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(12, 8, 12, 4)
        header.setSpacing(6)

        title = QLabel("Checklist")
        title.setStyleSheet(
            "font-family: 'Inter', sans-serif; font-size: 11px;"
            " color: #9CA3AF; font-weight: 500;"
        )
        header.addWidget(title)
        header.addStretch()

        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(20, 20)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(
            "QPushButton { border: none; font-size: 14px; color: #9CA3AF;"
            " border-radius: 10px; background: transparent; }"
            " QPushButton:hover { color: #EF4444; background: #FEE2E2; }"
        )
        delete_btn.clicked.connect(self._delete_checklist)
        header.addWidget(delete_btn)

        self._layout.addLayout(header)

        self._checkboxes_layout = QVBoxLayout()
        self._checkboxes_layout.setContentsMargins(0, 0, 0, 0)
        self._checkboxes_layout.setSpacing(0)
        self._layout.addLayout(self._checkboxes_layout)

        add_btn = QPushButton("+ Add item")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(
            "QPushButton { border: none; font-size: 12px; color: #CFA6D6;"
            " padding: 8px 12px; text-align: left;"
            " font-family: 'Inter', sans-serif; }"
            " QPushButton:hover { color: #9b59b6; }"
        )
        add_btn.clicked.connect(self._add_item)
        self._layout.addWidget(add_btn)

        self.adjustSize()

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
        widget.delete_requested.connect(self.object_delete_requested)
        self._checkboxes_layout.addWidget(widget)
        self.adjustSize()
        return obj

    def _delete_checklist(self):
        for i in range(self._checkboxes_layout.count()):
            widget = self._checkboxes_layout.itemAt(i).widget()
            if widget and hasattr(widget, "obj_id"):
                PageObjectRepo().delete(widget.obj_id)
        self.object_delete_requested.emit(self.checklist_id)
        self.deleteLater()

    def load_objects(self, objects):
        from src.ui.objects.checkbox_widget import CheckboxWidget

        for obj in objects:
            widget = CheckboxWidget(
                obj_id=obj.id,
                text=json.loads(obj.content).get("text", ""),
                checked=bool(obj.is_checked),
            )
            widget.changed.connect(self.object_changed)
            widget.delete_requested.connect(self.object_delete_requested)
            self._checkboxes_layout.addWidget(widget)
        self.adjustSize()


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
        action = menu.exec(self._add_btn.mapToGlobal(self._add_btn.rect().bottomLeft()))
        if action == checkbox_action:
            self._add_checklist()

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
            self._add_btn.hide()
        else:
            self._load_objects()
            self._checkbox_btn.show()
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

    def _group_objects_into_checklists(self):
        checklists = {}
        for obj in self._objects:
            cid = obj.sort_order // 100
            if cid not in checklists:
                checklists[cid] = []
            checklists[cid].append(obj)

        for cid, objs in sorted(checklists.items()):
            self._create_checklist_widget(cid, objs)

    def _create_checklist_widget(self, checklist_id, objects=None):
        widget = ChecklistWidget(
            checklist_id, page_id=self.current_page_id, parent=self.content
        )
        widget.object_changed.connect(self._on_object_changed)
        widget.object_delete_requested.connect(self._on_checklist_delete)
        if objects:
            widget.load_objects(objects)
        self._checklists[checklist_id] = widget

        canvas_w = self.content.width()
        container_w = min(400, canvas_w - 80)
        widget.setFixedWidth(container_w)
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

        obj = widget._add_item()
        self._objects.append(obj)
        self._page_empty_hint.hide()
        self._position_floating_button()

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

    def _clear_objects(self):
        self._objects = []
        for widget in self._checklists.values():
            widget.deleteLater()
        self._checklists.clear()

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

    def clear_editor(self):
        self.current_page_id = None
        self.page_title.setText("Select a page")
        self.welcome_label.show()
        self._page_empty_hint.hide()
        self._clear_toc()
        self._clear_objects()
        self._back_btn.hide()
        self._checkbox_btn.hide()
        self._add_btn.hide()
        self._parent_folder_id = None
        self._canvas_click_pos = None
        self.content.setPhotoBackground(True)
        self._center_welcome_label()

    def save_current(self):
        pass
