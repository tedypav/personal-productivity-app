from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

__all__ = ["EMOJI_DATA", "FunImportsDialog"]

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
