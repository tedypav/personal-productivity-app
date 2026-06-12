import os

from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


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
            if self.current_page_id is None:
                vp = self.scroll.viewport()
                self.content.setFixedWidth(vp.width())
                self.content.resize(vp.width(), vp.height())
            self._center_welcome_label()
            self._center_empty_hint()
        return super().eventFilter(obj, event)

    def _on_scroll(self, value):
        pass

    def _build_toolbar(self, parent_layout):
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet(
            "background: #FFF8F5; border-bottom: 1px solid #F0E6E8;"
        )
        from PyQt6.QtWidgets import QHBoxLayout, QPushButton

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

        parent_layout.addWidget(toolbar_widget)

    def _on_canvas_clicked(self, x, y):
        pass

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
        self._clear_toc()
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
        else:
            self._page_empty_hint.show()
            self._center_empty_hint()

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
            " color: #CFA6D6; background: transparent;"
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
        self._back_btn.hide()
        self._parent_folder_id = None
        self.content.setPhotoBackground(True)
        self._center_welcome_label()

    def save_current(self):
        pass
