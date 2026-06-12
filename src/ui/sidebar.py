import os

from PyQt6.QtCore import QDate, QMimeData, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.models.page import Page
from src.repositories.page_repo import PageRepo
from src.settings import load_settings
from src.ui.dialogs import create_dialog_header
from src.undo_manager import capture_page_tree, undo_manager


def _get_icon_path(name):
    """Get path to an icon file."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "assets",
        "icons",
        f"{name}.svg",
    )


class PageTreeWidget(QTreeWidget):
    """Custom tree widget that supports drag and drop for moving pages/folders."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._sidebar = None

    def set_sidebar(self, sidebar):
        """Set reference to sidebar for accessing repo and methods."""
        self._sidebar = sidebar

    def mimeTypes(self):
        return ["application/x-page-ids"]

    def mimeData(self, items):
        mime_data = QMimeData()
        page_ids = []
        for item in items:
            page_id = item.data(0, Qt.ItemDataRole.UserRole)
            if page_id:
                page_ids.append(str(page_id))
        mime_data.setData("application/x-page-ids", ",".join(page_ids).encode())
        return mime_data

    def dropEvent(self, event):
        if not self._sidebar:
            event.ignore()
            return

        mime_data = event.mimeData()
        if not mime_data.hasFormat("application/x-page-ids"):
            event.ignore()
            return

        page_ids_str = mime_data.data("application/x-page-ids").data().decode()
        page_ids = [int(pid) for pid in page_ids_str.split(",") if pid]
        if not page_ids:
            event.ignore()
            return

        target_item = self.itemAt(event.position().toPoint())
        target_folder_id = None

        if target_item:
            target_id = target_item.data(0, Qt.ItemDataRole.UserRole)

            if target_id in page_ids:
                event.ignore()
                return

            target_folder_id = target_id

        moved_any = False
        for page_id in page_ids:
            page = self._sidebar.repo.get_by_id(page_id)
            if not page:
                continue

            if page.page_type == "folder" and target_folder_id:
                if self._sidebar._is_descendant(page_id, target_folder_id):
                    continue

            # Prevent folders from being nested under pages
            if page.page_type == "folder" and target_folder_id:
                target_page = self._sidebar.repo.get_by_id(target_folder_id)
                if target_page and target_page.page_type != "folder":
                    continue

            current_parent = page.parent_id
            target_parent = target_folder_id
            if current_parent == target_parent:
                continue
            if current_parent is None and target_parent is None:
                continue
            if (
                current_parent is not None
                and target_parent is not None
                and int(current_parent) == int(target_parent)
            ):
                continue

            page.parent_id = target_folder_id
            self._sidebar.repo.update(page)
            moved_any = True

        if moved_any:
            self._sidebar._load_pages()
            self._sidebar.pages_changed.emit()
            event.acceptProposedAction()
        else:
            event.ignore()


EMOJI_DATA = {
    "Smileys": [
        "😀",
        "😃",
        "😄",
        "😁",
        "😆",
        "😅",
        "🤣",
        "😂",
        "🙂",
        "🙃",
        "😉",
        "😊",
        "😇",
        "🥰",
        "😍",
        "🤩",
        "😘",
        "😗",
        "😚",
        "😙",
        "🥲",
        "😋",
        "😛",
        "😜",
        "🤪",
        "😝",
        "🤑",
        "🤗",
        "🤭",
        "🫢",
        "🤫",
        "🤔",
        "🫡",
        "🤐",
        "🤨",
        "😐",
        "😑",
        "😶",
        "🫥",
        "😏",
        "😒",
        "🙄",
        "😬",
        "🤥",
        "😌",
        "😔",
        "😪",
        "🤤",
        "😴",
        "😷",
        "🤒",
        "🤕",
        "🤢",
        "🤮",
        "🥵",
        "🥶",
        "🥴",
        "😵",
        "🤯",
        "🤠",
        "🥳",
        "🥸",
        "😎",
        "🤓",
        "🧐",
    ],
    "Gestures": [
        "👋",
        "🤚",
        "🖐️",
        "✋",
        "🖖",
        "🫱",
        "🫲",
        "🫳",
        "🫴",
        "👌",
        "🤌",
        "🤏",
        "✌️",
        "🤞",
        "🫰",
        "🤟",
        "🤘",
        "🤙",
        "👈",
        "👉",
        "👆",
        "🖕",
        "👇",
        "☝️",
        "🫵",
        "👍",
        "👎",
        "✊",
        "👊",
        "🤛",
        "🤜",
        "👏",
        "🙌",
        "🫶",
        "👐",
        "🤲",
        "🤝",
        "🙏",
    ],
    "Hearts": [
        "❤️",
        "🧡",
        "💛",
        "💚",
        "💙",
        "💜",
        "🖤",
        "🤍",
        "🤎",
        "💔",
        "❤️‍🔥",
        "❤️‍🩹",
        "❣️",
        "💕",
        "💞",
        "💓",
        "💗",
        "💖",
        "💘",
        "💝",
    ],
    "Animals": [
        "🐶",
        "🐱",
        "🐭",
        "🐹",
        "🐰",
        "🦊",
        "🐻",
        "🐼",
        "🐻‍❄️",
        "🐨",
        "🐯",
        "🦁",
        "🐮",
        "🐷",
        "🐽",
        "🐸",
        "🐵",
        "🙈",
        "🙉",
        "🙊",
        "🐒",
        "🐔",
        "🐧",
        "🐦",
        "🐤",
        "🐣",
        "🐥",
        "🦆",
        "🦅",
        "🦉",
        "🦇",
        "🐺",
        "🐗",
        "🐴",
        "🦄",
        "🐝",
        "🪱",
        "🐛",
        "🦋",
        "🐌",
        "🐞",
    ],
    "Food": [
        "🍎",
        "🍐",
        "🍊",
        "🍋",
        "🍌",
        "🍉",
        "🍇",
        "🍓",
        "🫐",
        "🍈",
        "🍒",
        "🍑",
        "🥭",
        "🍍",
        "🥥",
        "🥝",
        "🍅",
        "🍆",
        "🥑",
        "🥦",
        "🥬",
        "🥒",
        "🌶️",
        "🫑",
        "🌽",
        "🥕",
        "🫒",
        "🧄",
        "🧅",
        "🥔",
        "🍠",
        "🫘",
        "🥜",
        "🍯",
        "🥛",
        "🍞",
        "🥐",
        "🥖",
        "🫓",
        "🥨",
        "🥯",
        "🥞",
        "🧇",
        "🧀",
        "🍖",
        "🍗",
        "🥩",
        "🥓",
        "🍔",
        "🍟",
        "🍕",
        "🌭",
        "🥪",
        "🌮",
        "🌯",
        "🫔",
        "🥙",
        "🧆",
        "🥚",
        "🍳",
        "🥘",
        "🍲",
        "🫕",
        "🥣",
        "🥗",
        "🍿",
        "🧈",
        "🧂",
        "🥫",
    ],
    "Activities": [
        "⚽",
        "🏀",
        "🏈",
        "⚾",
        "🥎",
        "🎾",
        "🏐",
        "🏉",
        "🥏",
        "🎱",
        "🪀",
        "🏓",
        "🏸",
        "🏒",
        "🏑",
        "🥍",
        "🏏",
        "🪃",
        "🥅",
        "⛳",
        "🪁",
        "🏹",
        "🎣",
        "🤿",
        "🥊",
        "🥋",
        "🎽",
        "🛹",
        "🛼",
        "🛷",
        "⛸️",
        "🥌",
        "🎿",
        "🎯",
        "🪀",
        "🪁",
        "🎮",
        "🕹️",
        "🎲",
        "🧩",
        "🎭",
        "🎨",
        "🧵",
        "🪡",
        "🧶",
        "🪆",
        "🎪",
    ],
    "Travel": [
        "🚗",
        "🚕",
        "🚙",
        "🚌",
        "🚎",
        "🏎️",
        "🚓",
        "🚑",
        "🚒",
        "🚐",
        "🛻",
        "🚚",
        "🚛",
        "🚜",
        "🏍️",
        "🛵",
        "🚲",
        "🛴",
        "🛺",
        "🚍",
        "🚘",
        "🚖",
        "🛩️",
        "✈️",
        "🛫",
        "🛬",
        "🪂",
        "💺",
        "🚀",
        "🛸",
        "🚁",
        "🛶",
        "⛵",
        "🚤",
        "🛥️",
        "🛳️",
        "⛴️",
        "🚢",
    ],
    "Objects": [
        "⌚",
        "📱",
        "📲",
        "💻",
        "⌨️",
        "🖥️",
        "🖨️",
        "🖱️",
        "🖲️",
        "🕹️",
        "🗜️",
        "💽",
        "💾",
        "💿",
        "📀",
        "📼",
        "📷",
        "📸",
        "📹",
        "🎥",
        "📽️",
        "🎞️",
        "📞",
        "☎️",
        "📟",
        "📠",
        "📺",
        "📻",
        "🎙️",
        "🎚️",
        "🎛️",
        "🧭",
        "⏱️",
        "⏲️",
        "⏰",
        "🕰️",
        "⌛",
        "⏳",
        "📡",
        "🔋",
        "🔌",
        "💡",
        "🔦",
        "🕯️",
    ],
}


class FunImportsDialog(QDialog):
    """Dialog for inserting emojis and GIFs."""

    def __init__(self, parent=None, target_edit=None):
        super().__init__(parent)
        self.setWindowTitle("Fun Imports")
        self.setMinimumSize(440, 520)
        self.target_edit = target_edit
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        emoji_tab_font = QFont("Segoe UI Emoji", 13)
        self.tabs.tabBar().setFont(emoji_tab_font)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 500;
                color: #9ca3af;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected {
                color: #CFA6D6;
                border-bottom: 2px solid #CFA6D6;
            }
            QTabBar::tab:hover { color: #7c3aed; }
        """)

        self.tabs.addTab(self._build_emoji_tab(), "😀 Emojis")
        self.tabs.addTab(self._build_gif_tab(), "🎬 GIFs")
        layout.addWidget(self.tabs)

    def _build_emoji_tab(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # Category bar
        cat_bar = QHBoxLayout()
        cat_bar.setSpacing(2)
        self._cat_buttons = {}
        categories = list(EMOJI_DATA.keys())
        cat_labels = {
            "Smileys": "😀",
            "Gestures": "👋",
            "Hearts": "❤️",
            "Animals": "🐶",
            "Food": "🍎",
            "Activities": "⚽",
            "Travel": "🚗",
            "Objects": "💻",
        }
        emoji_font = QFont("Segoe UI Emoji", 16)
        for cat in categories:
            btn = QLabel(cat_labels.get(cat, "😀"))
            btn.setFixedSize(36, 36)
            btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn.setToolTip(cat)
            btn.setFont(emoji_font)
            btn.setStyleSheet(
                "QLabel { border: none; border-radius: 6px; }"
                " QLabel:hover { background: #F3E8F6; }"
            )
            btn.mousePressEvent = lambda checked, c=cat: self._scroll_to_category(c)
            cat_bar.addWidget(btn)
            self._cat_buttons[cat] = btn
        cat_bar.addStretch()
        main_layout.addLayout(cat_bar)

        # Search
        self._emoji_search = QLineEdit()
        self._emoji_search.setPlaceholderText("Search emojis...")
        self._emoji_search.setClearButtonEnabled(True)
        self._emoji_search.textChanged.connect(self._filter_emojis)
        main_layout.addWidget(self._emoji_search)

        # Emoji grid
        self._emoji_scroll = QScrollArea()
        self._emoji_scroll.setWidgetResizable(True)
        self._emoji_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._emoji_container = QWidget()
        self._emoji_layout = QVBoxLayout(self._emoji_container)
        self._emoji_layout.setContentsMargins(0, 0, 0, 0)
        self._emoji_layout.setSpacing(8)
        self._emoji_scroll.setWidget(self._emoji_container)
        main_layout.addWidget(self._emoji_scroll, 1)

        self._build_emoji_grid()
        return widget

    def _build_emoji_grid(self):
        while self._emoji_layout.count():
            item = self._emoji_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        self._emoji_labels = []
        emoji_font = QFont("Segoe UI Emoji", 18)
        for category, emojis in EMOJI_DATA.items():
            cat_label = QLabel(category)
            cat_label.setStyleSheet(
                "font-size: 12px; font-weight: 600; color: #6b7280; padding: 4px 0px;"
            )
            cat_label.setProperty("category", category)
            self._emoji_layout.addWidget(cat_label)

            grid = QGridLayout()
            grid.setSpacing(2)
            grid.setContentsMargins(0, 0, 0, 0)
            for i, emoji in enumerate(emojis):
                btn = QLabel(emoji)
                btn.setFixedSize(40, 40)
                btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
                btn.setFont(emoji_font)
                btn.setStyleSheet(
                    "QLabel { border: none; border-radius: 6px; }"
                    " QLabel:hover { background: #F3E8F6; }"
                )
                btn.mousePressEvent = lambda checked, e=emoji: self._insert_emoji(e)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                grid.addWidget(btn, i // 8, i % 8)
                self._emoji_labels.append((btn, category))

            grid_widget = QWidget()
            grid_widget.setLayout(grid)
            grid_widget.setProperty("category", category)
            self._emoji_layout.addWidget(grid_widget)

        self._emoji_layout.addStretch()

    def _scroll_to_category(self, category):
        for i in range(self._emoji_layout.count()):
            item = self._emoji_layout.itemAt(i)
            widget = item.widget() if item else None
            if widget and widget.property("category") == category:
                self._emoji_scroll.ensureWidgetVisible(widget)
                break

    def _filter_emojis(self, text):
        for btn, category in self._emoji_labels:
            if text:
                btn.setVisible(text.lower() in category.lower() or text in btn.text())
            else:
                btn.setVisible(True)

    def _insert_emoji(self, emoji):
        if self.target_edit:
            try:
                self.target_edit.setFocus()
                cursor = self.target_edit.textCursor()
                cursor.insertText(emoji)
                self.target_edit.setTextCursor(cursor)
            except Exception:
                try:
                    self.target_edit.insertPlainText(emoji)
                except Exception:
                    pass
        self.accept()

    def _build_gif_tab(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # Search
        self._gif_search = QLineEdit()
        self._gif_search.setPlaceholderText("Search GIFs...")
        self._gif_search.setClearButtonEnabled(True)
        main_layout.addWidget(self._gif_search)

        # GIF grid (placeholder with sample categories)
        gif_scroll = QScrollArea()
        gif_scroll.setWidgetResizable(True)
        gif_scroll.setFrameShape(QFrame.Shape.NoFrame)
        gif_container = QWidget()
        gif_layout = QVBoxLayout(gif_container)
        gif_layout.setContentsMargins(0, 0, 0, 0)
        gif_layout.setSpacing(8)

        gif_categories = {
            "Trending": ["🎉", "🔥", "❤️", "😂", "👋", "👏", "🙌", "💪"],
            "Reactions": ["😮", "😍", "🥺", "😭", "🤣", "🙄", "😬", "🤔"],
            "Celebrations": ["🎊", "🥳", "🎆", "🎇", "🎈", "🎁", "🏆", "🎉"],
        }

        for cat_name, emojis in gif_categories.items():
            cat_label = QLabel(cat_name)
            cat_label.setStyleSheet(
                "font-size: 12px; font-weight: 600; color: #6b7280; padding: 4px 0px;"
            )
            gif_layout.addWidget(cat_label)

            grid = QGridLayout()
            grid.setSpacing(4)
            for i, em in enumerate(emojis):
                btn = QLabel(em)
                btn.setFixedSize(80, 80)
                btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
                btn.setFont(QFont("Segoe UI Emoji", 24))
                btn.setStyleSheet(
                    "QLabel { border: 1px solid #e5e7eb;"
                    " border-radius: 8px; background: #f9fafb; }"
                    " QLabel:hover { background: #F3E8F6;"
                    " border: 1px solid #CFA6D6; }"
                )
                btn.mousePressEvent = lambda checked, e=em: self._insert_gif(e)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                grid.addWidget(btn, i // 4, i % 4)
            grid_widget = QWidget()
            grid_widget.setLayout(grid)
            gif_layout.addWidget(grid_widget)

        gif_layout.addStretch()
        gif_scroll.setWidget(gif_container)
        main_layout.addWidget(gif_scroll, 1)
        return widget

    def _insert_gif(self, gif):
        if self.target_edit:
            self.target_edit.insertPlainText(f"[GIF: {gif}]")
        self.accept()


class Sidebar(QWidget):
    page_selected = pyqtSignal(int)
    pages_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.repo = PageRepo()
        self.settings = load_settings()
        self.setMinimumWidth(180)
        self._empty_hint = None
        self.setStyleSheet("""
            Sidebar {
                background: linear-gradient(#FFF8F5, #FFF0F5);
            }
            QTreeWidget {
                background: #FFFFFF;
                border: 1px solid #F7D1DC;
                border-radius: 12px;
                font-size: 13px;
                color: #2E2B2B;
                outline: none;
                padding: 4px;
            }
            QTreeWidget::item {
                padding: 7px 6px;
                border-radius: 8px;
                margin: 1px 2px;
                color: #2E2B2B;
            }
            QTreeWidget::item:selected {
                background-color: #F3E8F6;
                color: #2E2B2B;
            }
            QTreeWidget::item:hover {
                background-color: #FFF0F3;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #F7D1DC;
                border-radius: 16px;
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FFF5F7
                );
                font-size: 11px;
                font-weight: 500;
                color: #2E2B2B;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFF5F7, stop:1 #FFE4EC
                );
                border: 1px solid #F7AEC4;
            }
            QPushButton:pressed {
                background: #F7D1DC;
                border: 1px solid #CFA6D6;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(3)

        page_icon = QIcon(_get_icon_path("page"))
        folder_icon = QIcon(_get_icon_path("folder"))

        self.btn_new_folder = QPushButton("New Folder")
        self.btn_new_folder.setIcon(folder_icon)

        self.btn_new = QPushButton("New Page")
        self.btn_new.setIcon(page_icon)

        self.btn_new_page = QPushButton("Time Pages")
        self.btn_new_page.setIcon(page_icon)

        btn_layout.addWidget(self.btn_new_folder)
        btn_layout.addWidget(self.btn_new)
        btn_layout.addWidget(self.btn_new_page)
        layout.addLayout(btn_layout)

        btn_layout2 = QHBoxLayout()
        btn_layout2.setContentsMargins(0, 0, 0, 0)
        btn_layout2.setSpacing(3)
        self.btn_bulk_named = QPushButton("Name Pages")
        self.btn_bulk_named.setIcon(page_icon)

        archive_icon = QIcon(_get_icon_path("folder_archive"))
        self.btn_archive = QPushButton("Archive")
        self.btn_archive.setIcon(archive_icon)

        template_icon = QIcon(_get_icon_path("page_template"))
        self.btn_template = QPushButton("Set as Template")
        self.btn_template.setIcon(template_icon)

        btn_layout2.addWidget(self.btn_bulk_named)
        btn_layout2.addWidget(self.btn_archive)
        btn_layout2.addWidget(self.btn_template)
        btn_layout2.addStretch()
        layout.addLayout(btn_layout2)

        view_layout = QHBoxLayout()
        self.btn_expand = QPushButton("Show All")
        self.btn_collapse = QPushButton("Hide All")
        self.btn_expand.setStyleSheet(
            "QPushButton { padding: 4px 10px; font-size: 10px; border-radius: 14px; }"
        )
        self.btn_collapse.setStyleSheet(
            "QPushButton { padding: 4px 10px; font-size: 10px; border-radius: 14px; }"
        )
        view_layout.addWidget(self.btn_expand)
        view_layout.addWidget(self.btn_collapse)
        layout.addLayout(view_layout)

        self.tree = PageTreeWidget()
        self.tree.set_sidebar(self)
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.setAnimated(True)
        self.tree.setIconSize(QSize(20, 20))
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.template_tree = QTreeWidget()
        self.template_tree.setHeaderHidden(True)
        self.template_tree.setIndentation(16)
        self.template_tree.setAnimated(True)
        self.template_tree.setIconSize(QSize(20, 20))
        self.template_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.template_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.template_tree.itemClicked.connect(self._on_template_item_clicked)
        self.template_tree.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(pos, self.template_tree)
        )
        self.template_tree.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self._splitter = QSplitter(Qt.Orientation.Vertical)
        self._splitter.addWidget(self.tree)
        self._splitter.addWidget(self.template_tree)
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 1)

        saved_sizes = self.settings.get("sidebar_splitter_sizes")
        if saved_sizes:
            self._splitter.setSizes(saved_sizes)

        layout.addWidget(self._splitter, 1)

        self._splitter.splitterMoved.connect(self._save_splitter_sizes)

        self.btn_expand.clicked.connect(self._expand_all)
        self.btn_collapse.clicked.connect(self._collapse_all)

        self.btn_new.clicked.connect(self._create_page)
        self.btn_new_folder.clicked.connect(self._create_folder)
        self.btn_new_page.clicked.connect(self._bulk_creation_requested)
        self.btn_bulk_named.clicked.connect(self._bulk_named_dialog)
        self.btn_archive.clicked.connect(self._archive_selected)
        self.btn_template.clicked.connect(self._template_clicked)

        self._setup_shortcuts()
        self._ensure_special_folders()
        self._editor_ref = None
        self._load_pages()

    def set_editor(self, editor):
        """Set reference to the PageEditor for Fun Imports insertion."""
        self._editor_ref = editor

    def _save_splitter_sizes(self, pos, index):
        from src.settings import save_settings

        self.settings["sidebar_splitter_sizes"] = self._splitter.sizes()
        save_settings(self.settings)

    def _expand_all(self):
        self.tree.expandAll()

    def _collapse_all(self):
        self.tree.collapseAll()

    def _setup_shortcuts(self):
        delete_action = QAction("Delete", self.tree)
        delete_action.setShortcut(QKeySequence("Delete"))
        delete_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        delete_action.triggered.connect(self._delete_selected)
        self.tree.addAction(delete_action)
        self.template_tree.addAction(delete_action)

        rename_action = QAction("Rename", self.tree)
        rename_action.setShortcut(QKeySequence("F2"))
        rename_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        rename_action.triggered.connect(self._rename_selected)
        self.tree.addAction(rename_action)

    def _ensure_special_folders(self):
        from src.models.page import Page

        pages = self.repo.get_all()
        existing = {p.title for p in pages if p.page_type == "folder"}
        for title in ("Archive", "Fun Imports", "Templates"):
            if title not in existing:
                self.repo.create(Page(title=title, page_type="folder"))

    def _archive_selected(self):
        """Archive the currently selected item(s) from the upper tree."""
        selected = self.tree.selectedItems()
        if not selected:
            QMessageBox.information(
                self, "Archive", "Select a page or folder to archive."
            )
            return
        for item in selected:
            page_id = item.data(0, Qt.ItemDataRole.UserRole)
            page_type = item.data(0, Qt.ItemDataRole.UserRole + 1) or "page"
            page = self.repo.get_by_id(page_id)
            if page and page.title in ("Archive", "Templates", "Fun Imports"):
                continue
            self._archive_item(page_id, page_type)

    def _template_clicked(self):
        """Set the currently loaded page as a template."""
        if self._editor_ref and self._editor_ref.current_page_id:
            page_id = self._editor_ref.current_page_id
            page = self.repo.get_by_id(page_id)
            if page and page.page_type == "page":
                self._set_as_template(page_id)
            else:
                QMessageBox.information(
                    self, "Template", "Select a page to save as template."
                )
        else:
            QMessageBox.information(
                self, "Template", "Select a page to save as template."
            )

    def _load_pages(self):
        expanded_ids = self._collect_expanded(self.tree)
        template_expanded_ids = self._collect_expanded(self.template_tree)
        self.tree.clear()
        self.template_tree.clear()
        pages = self.repo.get_all()
        root_pages = [p for p in pages if p.parent_id is None]

        folder_icon = QIcon(_get_icon_path("folder"))
        page_icon = QIcon(_get_icon_path("page"))
        template_page_icon = QIcon(_get_icon_path("page_template"))
        archive_icon = QIcon(_get_icon_path("folder_archive"))
        fun_icon = QIcon(_get_icon_path("folder_fun"))
        template_icon = QIcon(_get_icon_path("folder_template"))

        children_map = {}
        for p in pages:
            children_map.setdefault(p.parent_id, []).append(p)

        folder_icons = {
            "Archive": archive_icon,
            "Fun Imports": fun_icon,
            "Templates": template_icon,
        }

        def _page_icon(page):
            if page.page_type == "folder":
                return folder_icons.get(page.title, folder_icon)
            if page.page_type == "template_page":
                return template_page_icon
            return page_icon

        def _make_item(parent, page):
            item = QTreeWidgetItem(parent)
            item.setIcon(0, _page_icon(page))
            item.setText(0, page.title)
            if page.page_type == "folder":
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
            item.setData(0, Qt.ItemDataRole.UserRole, page.id)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, page.page_type)
            return item

        def add_children(parent_item, parent_id):
            children = children_map.get(parent_id, [])
            for page in sorted(children, key=lambda x: x.title.lower()):
                _make_item(parent_item, page)
                add_children(parent_item.child(parent_item.childCount() - 1), page.id)

        # Separate special folders from regular pages
        special_titles = {"Fun Imports", "Archive", "Templates"}
        special_root = [
            p
            for p in root_pages
            if p.title in special_titles and p.page_type == "folder"
        ]
        regular_root = [p for p in root_pages if p.title not in special_titles]

        # Upper tree: regular pages/folders
        for page in sorted(regular_root, key=lambda x: x.title.lower()):
            item = _make_item(self.tree, page)
            add_children(item, page.id)

        # Lower tree: special folders
        for page in sorted(special_root, key=lambda x: x.title.lower()):
            item = _make_item(self.template_tree, page)
            add_children(item, page.id)

        if expanded_ids:
            self._restore_expanded(self.tree, expanded_ids)
        else:
            self.tree.expandAll()
        if template_expanded_ids:
            self._restore_expanded(self.template_tree, template_expanded_ids)
        has_pages = self.tree.topLevelItemCount() > 0
        has_templates = self.template_tree.topLevelItemCount() > 0
        if not has_pages and not has_templates:
            if not self._empty_hint:
                self._empty_hint = QLabel("No pages yet.\nClick + to create one.")
                self._empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._empty_hint.setStyleSheet(
                    "color: #9CA3AF; font-size: 13px; padding: 20px;"
                )
                self.layout().addWidget(self._empty_hint)
        elif self._empty_hint:
            self._empty_hint.hide()

    def _collect_expanded(self, tree=None):
        if tree is None:
            tree = self.tree
        ids = set()
        root = tree.invisibleRootItem()
        stack = [root]
        while stack:
            parent = stack.pop()
            for i in range(parent.childCount()):
                child = parent.child(i)
                pid = child.data(0, Qt.ItemDataRole.UserRole)
                if child.isExpanded() and pid:
                    ids.add(pid)
                stack.append(child)
        return ids

    def _restore_expanded(self, tree, ids):
        root = tree.invisibleRootItem()
        stack = [root]
        while stack:
            parent = stack.pop()
            for i in range(parent.childCount()):
                child = parent.child(i)
                pid = child.data(0, Qt.ItemDataRole.UserRole)
                if pid and pid in ids:
                    child.setExpanded(True)
                stack.append(child)

    def _on_item_clicked(self, item, column):
        page_id = item.data(0, Qt.ItemDataRole.UserRole)
        if page_id:
            self.page_selected.emit(page_id)

    def _on_template_item_clicked(self, item, column):
        page_title = item.text(0)
        if page_title == "Fun Imports":
            self._open_fun_imports()

    def _open_fun_imports(self):
        dialog = FunImportsDialog(self, target_edit=None)
        dialog.exec()

    def _get_unique_name(self, base_name, parent_id, exclude_id=None):
        """Get a unique name by appending (N) if needed."""
        name = base_name
        counter = 1
        while self.repo.has_sibling_with_name(parent_id, name, exclude_id):
            name = f"{base_name} ({counter})"
            counter += 1
        return name

    def _create_page(self):
        title, ok = QInputDialog.getText(self, "New Page", "Page title:")
        if ok and title.strip():
            selected = self.tree.selectedItems()
            if selected:
                for item in selected:
                    parent_id = item.data(0, Qt.ItemDataRole.UserRole)
                    unique_name = self._get_unique_name(title.strip(), parent_id)
                    self.repo.create(
                        Page(title=unique_name, parent_id=parent_id, page_type="page")
                    )
            else:
                unique_name = self._get_unique_name(title.strip(), None)
                self.repo.create(Page(title=unique_name, page_type="page"))
            self._load_pages()
            self.pages_changed.emit()

    def _create_folder(self):
        title, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and title.strip():
            selected = self.tree.selectedItems()
            if selected:
                for item in selected:
                    parent_id = item.data(0, Qt.ItemDataRole.UserRole)
                    page_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
                    if page_type == "folder":
                        unique_name = self._get_unique_name(title.strip(), parent_id)
                        self.repo.create(
                            Page(
                                title=unique_name,
                                parent_id=parent_id,
                                page_type="folder",
                            )
                        )
                    else:
                        unique_name = self._get_unique_name(title.strip(), None)
                        self.repo.create(Page(title=unique_name, page_type="folder"))
            else:
                unique_name = self._get_unique_name(title.strip(), None)
                self.repo.create(Page(title=unique_name, page_type="folder"))
            self._load_pages()
            self.pages_changed.emit()

    def _bulk_creation_requested(self):
        self._bulk_create_dialog()

    def _bulk_create_dialog(self):
        from PyQt6.QtWidgets import (
            QComboBox,
            QDateEdit,
            QDialog,
            QDialogButtonBox,
            QLabel,
            QVBoxLayout,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Bulk Create Pages")

        title_layout = create_dialog_header("Bulk Create Pages")

        layout = QVBoxLayout(dialog)
        layout.addLayout(title_layout)

        mode_combo = QComboBox()
        mode_combo.addItems(["Days", "Weeks", "Years"])
        layout.addWidget(QLabel("Mode:"))
        layout.addWidget(mode_combo)

        start_date = QDateEdit()
        start_date.setCalendarPopup(True)
        start_date.setDate(QDate.currentDate())
        start_date.setDisplayFormat("yyyy-MM-dd")
        calendar_style = """
            QDateEdit {
                padding: 6px 12px;
                border: 1px solid #F0E6E8;
                border-radius: 10px;
                background: #FFFFFF;
                font-size: 13px;
                color: #2E2B2B;
                min-width: 120px;
                font-family: 'Inter', 'Poppins', sans-serif;
            }
            QDateEdit::drop-down {
                border: none;
                width: 28px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }
            QDateEdit::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid #CFA6D6;
                margin-right: 8px;
            }
            QCalendarWidget {
                background: #FFFFFF;
                border: 1px solid #F0E6E8;
                border-radius: 12px;
                font-family: 'Inter', 'Poppins', sans-serif;
                font-size: 10px;
            }
            QCalendarWidget QToolButton {
                color: #2E2B2B;
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 3px 6px;
                font-size: 11px;
                font-family: 'Inter', 'Poppins', sans-serif;
            }
            QCalendarWidget QToolButton:hover {
                background: #FFF0F3;
            }
            QCalendarWidget QToolButton:pressed {
                background: #F7D1DC;
            }
            QCalendarWidget QToolButton#qt_calendar_prevmonth,
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                qproperty-icon: none;
                min-width: 22px;
                font-size: 11px;
                color: #CFA6D6;
            }
            QCalendarWidget QToolButton#qt_calendar_prevmonth { qproperty-text: "<"; }
            QCalendarWidget QToolButton#qt_calendar_nextmonth { qproperty-text: ">"; }
            QCalendarWidget QToolButton#qt_calendar_prevmonth:hover,
            QCalendarWidget QToolButton#qt_calendar_nextmonth:hover {
                color: #2E2B2B;
                background: #FFF0F3;
            }
            QCalendarWidget QToolButton#qt_calendar_monthbutton,
            QCalendarWidget QToolButton#qt_calendar_yearbutton {
                font-size: 11px;
                font-weight: 600;
                min-width: 60px;
                color: #2E2B2B;
            }
            QCalendarWidget QWidget#qt_calendar_calendarview {
                background: #FFFFFF;
                border: none;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #2E2B2B;
                background: #FFFFFF;
                selection-background-color: #CFA6D6;
                selection-color: #FFFFFF;
                font-family: 'Inter', 'Poppins', sans-serif;
                font-size: 10px;
                gridline-color: transparent;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #D1D5DB;
            }
            QCalendarWidget QAbstractItemView:focus {
                outline: none;
            }
            QCalendarWidget QTableView {
                selection-background-color: #CFA6D6;
                selection-color: #FFFFFF;
            }
            QCalendarWidget QTableView QHeaderView::section {
                background: #FFF8F5;
                color: #6B6770;
                border: none;
                border-bottom: 1px solid #F0E6E8;
                padding: 2px;
                font-size: 9px;
                font-weight: 600;
                font-family: 'Inter', 'Poppins', sans-serif;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: #FFF8F5;
                border-top: 1px solid #F0E6E8;
                border-radius: 0 0 12px 12px;
                padding: 2px;
            }
            QCalendarWidget QCalendarDayWidget {
                padding: 0px;
                min-width: 24px;
                max-width: 28px;
                min-height: 18px;
                max-height: 22px;
            }
            QCalendarWidget QToolButton#qt_calendar_calendarbutton {
                qproperty-icon: none;
                min-width: 18px;
                font-size: 10px;
                color: #CFA6D6;
            }
        """
        start_date.setStyleSheet(calendar_style)
        # Style weekend days as pink/lavender
        from PyQt6.QtGui import QColor, QTextCharFormat

        start_cal = start_date.calendarWidget()
        if start_cal:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor("#CFA6D6"))
            start_cal.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, fmt)
            start_cal.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, fmt)
        layout.addWidget(QLabel("Start date:"))
        layout.addWidget(start_date)

        end_label = QLabel("End date:")
        end_date = QDateEdit()
        end_date.setCalendarPopup(True)
        end_date.setDate(QDate.currentDate())
        end_date.setDisplayFormat("yyyy-MM-dd")
        end_date.setStyleSheet(calendar_style)
        end_cal = end_date.calendarWidget()
        if end_cal:
            fmt_end = QTextCharFormat()
            fmt_end.setForeground(QColor("#CFA6D6"))
            end_cal.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, fmt_end)
            end_cal.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, fmt_end)
        layout.addWidget(end_label)
        layout.addWidget(end_date)

        week_start_label = QLabel("Week starts on:")
        week_start_combo = QComboBox()
        week_start_combo.addItems(
            [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
        )
        week_start_combo.setCurrentText(self.settings.get("week_start_day", "Monday"))
        week_start_label.setVisible(False)
        week_start_combo.setVisible(False)
        layout.addWidget(week_start_label)
        layout.addWidget(week_start_combo)

        def _update_end_date():
            mode = mode_combo.currentText()
            if mode == "Days":
                end_date.setDate(start_date.date().addDays(1))
            elif mode == "Weeks":
                end_date.setDate(start_date.date().addDays(7))
            elif mode == "Years":
                end_date.setDate(start_date.date().addYears(1))

        def on_mode_changed(index):
            is_weeks = mode_combo.currentText() == "Weeks"
            week_start_label.setVisible(is_weeks)
            week_start_combo.setVisible(is_weeks)
            _update_end_date()

        mode_combo.currentIndexChanged.connect(on_mode_changed)
        start_date.dateChanged.connect(_update_end_date)

        def _validate():
            mode = mode_combo.currentText()
            if mode == "Days" and end_date.date() <= start_date.date():
                end_date.setDate(start_date.date().addDays(1))
            elif mode == "Weeks" and end_date.date() < start_date.date().addDays(7):
                end_date.setDate(start_date.date().addDays(7))
            elif mode == "Years" and end_date.date() <= start_date.date().addYears(1):
                end_date.setDate(start_date.date().addYears(1))

        end_date.dateChanged.connect(_validate)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            mode = mode_combo.currentText()
            from datetime import timedelta

            start = start_date.date().toPyDate()
            end = end_date.date().toPyDate()

            # Get selected folder as parent
            selected_folder_id = None
            selected = self.tree.selectedItems()
            if selected:
                selected_folder_id = selected[0].data(0, Qt.ItemDataRole.UserRole)

            titles = []
            if mode == "Days":
                current = start
                while current <= end:
                    titles.append(current.strftime("%Y-%m-%d"))
                    current += timedelta(days=1)
            elif mode == "Weeks":
                week_days = {
                    "Monday": 0,
                    "Tuesday": 1,
                    "Wednesday": 2,
                    "Thursday": 3,
                    "Friday": 4,
                    "Saturday": 5,
                    "Sunday": 6,
                }
                target_wd = week_days[week_start_combo.currentText()]
                current = start
                while current.weekday() != target_wd:
                    current -= timedelta(days=1)
                while current <= end:
                    week_end = current + timedelta(days=6)
                    date_str = (
                        f"{current.strftime('%Y-%m-%d')}"
                        f" - {week_end.strftime('%Y-%m-%d')}"
                    )
                    titles.append(date_str)
                    current += timedelta(weeks=1)
            elif mode == "Years":
                for year in range(start.year, end.year + 1):
                    titles.append(str(year))

            for title in titles:
                self.repo.create(
                    Page(title=title, page_type="page", parent_id=selected_folder_id)
                )
            self._load_pages()
            self.pages_changed.emit()

    def _bulk_named_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Bulk Create Named Pages")

        title_layout = create_dialog_header("Bulk Create Named Pages")

        layout = QVBoxLayout(dialog)
        layout.addLayout(title_layout)

        layout.addWidget(QLabel("Base name:"))
        name_edit = QLineEdit("Page")
        layout.addWidget(name_edit)

        layout.addWidget(QLabel("Number of pages:"))
        count_spin = QSpinBox()
        count_spin.setRange(1, 999)
        count_spin.setValue(5)
        layout.addWidget(count_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            base = name_edit.text().strip()
            count = count_spin.value()
            if not base:
                return
            # Get selected folder as parent
            selected_folder_id = None
            selected = self.tree.selectedItems()
            if selected:
                selected_folder_id = selected[0].data(0, Qt.ItemDataRole.UserRole)
            for i in range(1, count + 1):
                self.repo.create(
                    Page(
                        title=f"{base} {i}",
                        page_type="page",
                        parent_id=selected_folder_id,
                    )
                )
            self._load_pages()
            self.pages_changed.emit()

    def _show_context_menu(self, pos, tree=None):
        if tree is None:
            tree = self.tree
        item = tree.itemAt(pos)
        if not item:
            return

        selected = tree.selectedItems()
        page_id = item.data(0, Qt.ItemDataRole.UserRole)
        page_type = item.data(0, Qt.ItemDataRole.UserRole + 1) or "page"
        menu = QMenu()

        if len(selected) > 1:
            delete_sel = menu.addAction(f"Delete Selected ({len(selected)})")
            action = menu.exec(tree.viewport().mapToGlobal(pos))
            if action == delete_sel:
                self._bulk_delete(selected)
            return

        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        menu.addSeparator()
        add_child_action = menu.addAction("Add Child Page")
        add_folder_action = None
        if page_type == "folder":
            add_folder_action = menu.addAction("Add Child Folder")
        menu.addSeparator()
        set_template_action = menu.addAction("Set as Template")
        menu.addSeparator()
        archive_action = menu.addAction("Archive")
        menu.addSeparator()
        move_action = menu.addAction("Move to Folder...")
        menu.addSeparator()
        move_up_action = menu.addAction("Move Up")
        move_down_action = menu.addAction("Move Down")

        action = menu.exec(tree.viewport().mapToGlobal(pos))

        if action == rename_action:
            current = item.text(0)
            if page_type == "folder":
                current = current.replace("📁 ", "", 1)
            title, ok = QInputDialog.getText(self, "Rename", "New name:", text=current)
            if ok and title.strip():
                page = self.repo.get_by_id(page_id)
                if page:
                    new_name = title.strip()
                    if self.repo.has_sibling_with_name(
                        page.parent_id, new_name, exclude_id=page_id
                    ):
                        new_name = self._get_unique_name(
                            new_name, page.parent_id, exclude_id=page_id
                        )
                    page.title = new_name
                    self.repo.update(page)
                    self._load_pages()
                    self.pages_changed.emit()

        elif action == delete_action:
            data = capture_page_tree(page_id)
            if data:
                data["type"] = "page"
                undo_manager.push(data)
            self.repo.delete(page_id)
            self._load_pages()
            self.pages_changed.emit()

        elif action == add_child_action:
            title, ok = QInputDialog.getText(self, "New Child Page", "Page title:")
            if ok and title.strip():
                page = Page(title=title.strip(), parent_id=page_id, page_type="page")
                self.repo.create(page)
                self._load_pages()
                self.pages_changed.emit()

        elif action == add_folder_action:
            title, ok = QInputDialog.getText(self, "New Child Folder", "Folder name:")
            if ok and title.strip():
                page = Page(title=title.strip(), parent_id=page_id, page_type="folder")
                self.repo.create(page)
                self._load_pages()
                self.pages_changed.emit()

        elif action == move_action:
            self._move_to_folder(page_id, page_type)

        elif action == move_up_action:
            page = self.repo.get_by_id(page_id)
            if page:
                page.sort_order = max(0, page.sort_order - 1)
                self.repo.update(page)
                self._load_pages()
                self.pages_changed.emit()

        elif action == move_down_action:
            page = self.repo.get_by_id(page_id)
            if page:
                page.sort_order += 1
                self.repo.update(page)
                self._load_pages()
                self.pages_changed.emit()

        elif action == archive_action:
            page = self.repo.get_by_id(page_id)
            if page and page.title in ("Archive", "Templates", "Fun Imports"):
                QMessageBox.information(
                    self, "Archive", f"Cannot archive the {page.title} folder."
                )
            else:
                self._archive_item(page_id, page_type)

        elif action == set_template_action:
            self._set_as_template(page_id)

    def _archive_item(self, page_id, page_type):
        """Archive a page or folder."""
        if page_type == "folder":
            page = self.repo.get_by_id(page_id)
            if page:
                pages = self.repo.get_all()
                archive_folder = [
                    p for p in pages if p.title == "Archive" and p.page_type == "folder"
                ]
                archive_id = (
                    archive_folder[0].id
                    if archive_folder
                    else self.repo.create(Page(title="Archive", page_type="folder"))
                )
                existing = [
                    p
                    for p in pages
                    if p.title == page.title
                    and p.parent_id == archive_id
                    and p.page_type == "folder"
                    and p.id != page_id
                ]
                if existing:
                    target_id = existing[0].id
                    children = self.repo.get_children(page_id)
                    for child in children:
                        child.parent_id = target_id
                        self.repo.update(child)
                    self.repo.delete(page_id)
                else:
                    page.parent_id = archive_id
                    self.repo.update(page)
        else:
            pages = self.repo.get_all()
            archive_folder = [
                p for p in pages if p.title == "Archive" and p.page_type == "folder"
            ]
            archive_id = (
                archive_folder[0].id
                if archive_folder
                else self.repo.create(Page(title="Archive", page_type="folder"))
            )
            page = self.repo.get_by_id(page_id)
            if page:
                if page.parent_id:
                    parent_page = self.repo.get_by_id(page.parent_id)
                    if parent_page:
                        existing = [
                            p
                            for p in pages
                            if p.title == parent_page.title
                            and p.parent_id == archive_id
                            and p.page_type == "folder"
                        ]
                        if existing:
                            target_folder_id = existing[0].id
                        else:
                            target_folder_id = self.repo.create(
                                Page(
                                    title=parent_page.title,
                                    parent_id=archive_id,
                                    page_type="folder",
                                )
                            )
                        unique_name = self._get_unique_name(
                            page.title,
                            target_folder_id,
                            exclude_id=page_id,
                        )
                        page.title = unique_name
                        page.parent_id = target_folder_id
                        self.repo.update(page)
                else:
                    unique_name = self._get_unique_name(
                        page.title, archive_id, exclude_id=page_id
                    )
                    page.title = unique_name
                    page.parent_id = archive_id
                    self.repo.update(page)

        self._load_pages()
        self.pages_changed.emit()

    def _set_as_template(self, page_id):
        """Copy a page to the Templates folder as a template."""
        page = self.repo.get_by_id(page_id)
        if not page:
            return

        pages = self.repo.get_all()
        templates_folder = [
            p for p in pages if p.title == "Templates" and p.page_type == "folder"
        ]
        templates_id = (
            templates_folder[0].id
            if templates_folder
            else self.repo.create(Page(title="Templates", page_type="folder"))
        )

        template_name = self._get_unique_name(page.title, templates_id)
        new_page = Page(
            title=template_name,
            parent_id=templates_id,
            page_type="template_page",
        )
        self.repo.create(new_page)
        self._load_pages()
        self.pages_changed.emit()
        QMessageBox.information(
            self,
            "Template",
            f"Page {template_name} saved as a template.",
        )

    def _move_to_folder(self, page_id, page_type):
        """Show dialog to move page/folder to another folder or root."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Move to Folder")
        dialog.setMinimumWidth(300)
        dialog.setMinimumHeight(400)

        title_layout = create_dialog_header("Move to Folder")

        layout = QVBoxLayout(dialog)
        layout.addLayout(title_layout)

        # Add tree widget to show folder structure
        folder_tree = QTreeWidget()
        folder_tree.setHeaderHidden(True)
        folder_tree.setIndentation(16)

        # Add root option
        root_item = QTreeWidgetItem(folder_tree)
        root_item.setIcon(0, QIcon(_get_icon_path("folder")))
        root_item.setText(0, "Root (no folder)")
        root_item.setData(0, Qt.ItemDataRole.UserRole, None)

        # Get all folders
        all_pages = self.repo.get_all()
        folders = [p for p in all_pages if p.page_type == "folder" and p.id != page_id]

        def add_folder_children(parent_item, parent_id):
            children = [f for f in folders if f.parent_id == parent_id]
            for folder in sorted(children, key=lambda x: x.sort_order):
                item = QTreeWidgetItem(parent_item)
                item.setIcon(0, QIcon(_get_icon_path("folder")))
                item.setText(0, folder.title)
                item.setData(0, Qt.ItemDataRole.UserRole, folder.id)
                add_folder_children(item, folder.id)

        # Add all root-level folders
        root_folders = [f for f in folders if f.parent_id is None]
        for folder in sorted(root_folders, key=lambda x: x.sort_order):
            item = QTreeWidgetItem(folder_tree)
            item.setIcon(0, QIcon(_get_icon_path("folder")))
            item.setText(0, folder.title)
            item.setData(0, Qt.ItemDataRole.UserRole, folder.id)
            add_folder_children(item, folder.id)

        folder_tree.expandAll()
        layout.addWidget(folder_tree)

        # Add buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_items = folder_tree.selectedItems()
            if selected_items:
                target_folder_id = selected_items[0].data(0, Qt.ItemDataRole.UserRole)

                # Prevent moving folder into itself or its descendants
                if page_type == "folder" and target_folder_id:
                    if self._is_descendant(page_id, target_folder_id):
                        QMessageBox.warning(
                            self,
                            "Invalid Move",
                            "Cannot move a folder into itself or its descendants.",
                        )
                        return

                # Move the page/folder
                page = self.repo.get_by_id(page_id)
                if page:
                    page.parent_id = target_folder_id
                    self.repo.update(page)
                    self._load_pages()
                    self.pages_changed.emit()

    def _is_descendant(self, folder_id, potential_descendant_id):
        """Check if potential_descendant_id is a descendant of folder_id."""
        if folder_id == potential_descendant_id:
            return True

        # Get all children of folder_id
        children = self.repo.get_children(folder_id)
        for child in children:
            if child.id == potential_descendant_id:
                return True
            if child.page_type == "folder":
                if self._is_descendant(child.id, potential_descendant_id):
                    return True
        return False

    def _bulk_delete(self, items):
        all_ids = []
        for item in items:
            pid = item.data(0, Qt.ItemDataRole.UserRole)
            if pid:
                all_ids.append(pid)
        if not all_ids:
            return

        selected_set = set(all_ids)
        to_capture = []
        for pid in all_ids:
            page = self.repo.get_by_id(pid)
            if page and page.parent_id not in selected_set:
                to_capture.append(pid)

        captured = []
        for pid in to_capture:
            data = capture_page_tree(pid)
            if data:
                data["type"] = "page"
                captured.append(data)

        if captured:
            undo_manager.push({"type": "bulk", "actions": captured})

        # Delete all pages
        for pid in all_ids:
            self.repo.delete(pid)
        if self._editor_ref and self._editor_ref.current_page_id in all_ids:
            self._editor_ref.clear_editor()
        self._load_pages()
        self.pages_changed.emit()

    def delete_selected(self):
        items = self.tree.selectedItems() + self.template_tree.selectedItems()
        if len(items) > 1:
            self._bulk_delete(items)
        elif len(items) == 1:
            item = items[0]
            page_id = item.data(0, Qt.ItemDataRole.UserRole)
            data = capture_page_tree(page_id)
            if data:
                data["type"] = "page"
                undo_manager.push(data)
            self.repo.delete(page_id)
            self._load_pages()
            self.pages_changed.emit()

    def _delete_selected(self):
        items = self.tree.selectedItems() + self.template_tree.selectedItems()
        if not items:
            return
        if len(items) > 1:
            self._bulk_delete(items)
        else:
            item = items[0]
            page_id = item.data(0, Qt.ItemDataRole.UserRole)
            data = capture_page_tree(page_id)
            if data:
                data["type"] = "page"
                undo_manager.push(data)
            self.repo.delete(page_id)
            if self._editor_ref and self._editor_ref.current_page_id == page_id:
                self._editor_ref.clear_editor()
            self._load_pages()
            self.pages_changed.emit()

    def _rename_selected(self):
        items = self.tree.selectedItems()
        if not items or len(items) != 1:
            return
        item = items[0]
        page_id = item.data(0, Qt.ItemDataRole.UserRole)
        current = item.text(0)
        title, ok = QInputDialog.getText(self, "Rename", "New name:", text=current)
        if ok and title.strip():
            page = self.repo.get_by_id(page_id)
            if page:
                page.title = title.strip()
                self.repo.update(page)
                self._load_pages()
                self.pages_changed.emit()

    def refresh(self):
        self._load_pages()
