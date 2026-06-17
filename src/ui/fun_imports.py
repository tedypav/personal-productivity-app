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
        self.tabs.setObjectName("funImportsTabs")
        emoji_tab_font = QFont("Segoe UI Emoji", 13)
        self.tabs.tabBar().setObjectName("funImportsTabBar")
        self.tabs.tabBar().setFont(emoji_tab_font)

        self.tabs.addTab(self._build_emoji_tab(), "😀 Emojis")
        self.tabs.addTab(self._build_gif_tab(), "🎬 GIFs")
        self.tabs.addTab(self._build_upload_tab(), "📤 Upload")
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
            btn.setObjectName("funImportsCatBtn")
            btn.setFixedSize(36, 36)
            btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn.setToolTip(cat)
            btn.setFont(emoji_font)
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
                btn.setObjectName("funImportsEmojiBtn")
                btn.setFixedSize(40, 40)
                btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
                btn.setFont(emoji_font)
                btn.mousePressEvent = lambda checked, e=emoji: self._insert_emoji(e)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                grid.addWidget(btn, i // 8, i % 8)
                self._emoji_labels.append((btn, category))

            grid_widget = QWidget()
            grid_widget.setLayout(grid)
            grid_widget.setProperty("category", category)
            self._emoji_layout.addWidget(grid_widget)

        self._build_custom_emoji_section(self._emoji_layout)
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
                    import sys

                    print(f"Failed to insert emoji: {emoji}", file=sys.stderr)
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
        self._gif_layout = QVBoxLayout(gif_container)
        self._gif_layout.setContentsMargins(0, 0, 0, 0)
        self._gif_layout.setSpacing(8)

        gif_categories = {
            "Trending": ["🎉", "🔥", "❤️", "😂", "👋", "👏", "🙌", "💪"],
            "Reactions": ["😮", "😍", "🥺", "😭", "🤣", "🙄", "😬", "🤔"],
            "Celebrations": ["🎊", "🥳", "🎆", "🎇", "🎈", "🎁", "🏆", "🎉"],
        }

        for cat_name, emojis in gif_categories.items():
            cat_label = QLabel(cat_name)
            cat_label.setObjectName("funImportsCatLabel")
            self._gif_layout.addWidget(cat_label)

            grid = QGridLayout()
            grid.setSpacing(4)
            for i, em in enumerate(emojis):
                btn = QLabel(em)
                btn.setObjectName("funImportsGifBtn")
                btn.setFixedSize(80, 80)
                btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
                btn.setFont(QFont("Segoe UI Emoji", 24))
                btn.mousePressEvent = lambda checked, e=em: self._insert_gif(e)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                grid.addWidget(btn, i // 4, i % 4)
            grid_widget = QWidget()
            grid_widget.setLayout(grid)
            self._gif_layout.addWidget(grid_widget)

        self._build_custom_gif_section(self._gif_layout)
        self._gif_layout.addStretch()
        gif_scroll.setWidget(gif_container)
        main_layout.addWidget(gif_scroll, 1)
        return widget

    def _get_upload_dir(self, kind):
        import os

        base = os.path.join(
            os.path.dirname(__file__), "..", "..", "assets", "custom", kind
        )
        os.makedirs(base, exist_ok=True)
        return base

    def _get_custom_files(self, kind):
        import os

        upload_dir = self._get_upload_dir(kind)
        return sorted(
            f
            for f in os.listdir(upload_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg"))
        )

    def _build_custom_emoji_section(self, layout):
        import os

        from PyQt6.QtGui import QPixmap

        files = self._get_custom_files("emojis")
        if not files:
            return

        cat_label = QLabel("Custom")
        cat_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #6b7280;" " padding: 4px 0px;"
        )
        layout.addWidget(cat_label)

        grid = QGridLayout()
        grid.setSpacing(2)
        grid.setContentsMargins(0, 0, 0, 0)
        for i, fname in enumerate(files):
            path = os.path.join(self._get_upload_dir("emojis"), fname)
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)

            btn = QLabel()
            btn.setObjectName("funImportsEmojiBtn")
            btn.setFixedSize(40, 40)
            btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                btn.setPixmap(
                    pixmap.scaled(
                        36,
                        36,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(fname)
            btn.mousePressEvent = lambda checked, p=path: self._insert_emoji(p)
            container_layout.addWidget(btn)

            del_btn = QLabel("×")
            del_btn.setFixedSize(16, 16)
            del_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            del_btn.setStyleSheet(
                "color: #9CA3AF; font-size: 12px; background: transparent;"
            )
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.mousePressEvent = lambda checked, p=path: self._delete_custom_item(
                p, "emojis"
            )
            container_layout.addWidget(del_btn)

            grid.addWidget(container, i // 8, i % 8)

        grid_widget = QWidget()
        grid_widget.setLayout(grid)
        layout.addWidget(grid_widget)

    def _build_custom_gif_section(self, layout):
        import os

        from PyQt6.QtGui import QMovie, QPixmap

        files = self._get_custom_files("gifs")
        if not files:
            return

        cat_label = QLabel("Custom")
        cat_label.setObjectName("funImportsCatLabel")
        layout.addWidget(cat_label)

        grid = QGridLayout()
        grid.setSpacing(4)
        for i, fname in enumerate(files):
            path = os.path.join(self._get_upload_dir("gifs"), fname)
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)

            btn = QLabel()
            btn.setObjectName("funImportsGifBtn")
            btn.setFixedSize(80, 80)
            btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if fname.lower().endswith(".gif"):
                movie = QMovie(path)
                if movie.isValid():
                    movie.setScaledSize(
                        btn.size() if btn.size().isValid() else (76, 76)
                    )
                    btn.setMovie(movie)
                    movie.start()
                else:
                    pixmap = QPixmap(path)
                    if not pixmap.isNull():
                        btn.setPixmap(
                            pixmap.scaled(
                                76,
                                76,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation,
                            )
                        )
            else:
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    btn.setPixmap(
                        pixmap.scaled(
                            76,
                            76,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(fname)
            btn.mousePressEvent = lambda checked, p=path: self._insert_gif(p)

            del_btn = QLabel("×")
            del_btn.setFixedSize(16, 16)
            del_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            del_btn.setStyleSheet(
                "color: #9CA3AF; font-size: 12px; background: transparent;"
            )
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.mousePressEvent = lambda checked, p=path: self._delete_custom_item(
                p, "gifs"
            )

            wrapper = QWidget()
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)
            wrapper_layout.setSpacing(0)
            wrapper_layout.addWidget(btn)
            wrapper_layout.addWidget(del_btn)

            grid.addWidget(wrapper, i // 4, i % 4)

        grid_widget = QWidget()
        grid_widget.setLayout(grid)
        layout.addWidget(grid_widget)

    def _delete_custom_item(self, path, kind):
        import os

        os.remove(path)
        self._refresh_custom_sections()

    def _refresh_custom_sections(self):
        self._build_emoji_grid()
        self._rebuild_gif_content()

    def _rebuild_gif_content(self):
        while self._gif_layout.count():
            item = self._gif_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        gif_categories = {
            "Trending": ["🎉", "🔥", "❤️", "😂", "👋", "👏", "🙌", "💪"],
            "Reactions": ["😮", "😍", "🥺", "😭", "🤣", "🙄", "😬", "🤔"],
            "Celebrations": ["🎊", "🥳", "🎆", "🎇", "🎈", "🎁", "🏆", "🎉"],
        }

        for cat_name, emojis in gif_categories.items():
            cat_label = QLabel(cat_name)
            cat_label.setObjectName("funImportsCatLabel")
            self._gif_layout.addWidget(cat_label)

            grid = QGridLayout()
            grid.setSpacing(4)
            for i, em in enumerate(emojis):
                btn = QLabel(em)
                btn.setObjectName("funImportsGifBtn")
                btn.setFixedSize(80, 80)
                btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
                btn.setFont(QFont("Segoe UI Emoji", 24))
                btn.mousePressEvent = lambda checked, e=em: self._insert_gif(e)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                grid.addWidget(btn, i // 4, i % 4)
            grid_widget = QWidget()
            grid_widget.setLayout(grid)
            self._gif_layout.addWidget(grid_widget)

        self._build_custom_gif_section(self._gif_layout)
        self._gif_layout.addStretch()

    def _upload_emoji(self):
        from PyQt6.QtWidgets import QFileDialog

        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Emoji Images",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.svg)",
        )
        if paths:
            import shutil

            upload_dir = self._get_upload_dir("emojis")
            for path in paths:
                shutil.copy2(path, upload_dir)
            self._refresh_custom_sections()

    def _upload_gif(self):
        from PyQt6.QtWidgets import QFileDialog

        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select GIF Files",
            "",
            "GIFs (*.gif)",
        )
        if paths:
            import shutil

            upload_dir = self._get_upload_dir("gifs")
            for path in paths:
                shutil.copy2(path, upload_dir)
            self._refresh_custom_sections()

    def _build_upload_tab(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        from PyQt6.QtWidgets import QPushButton

        emoji_label = QLabel("Upload Custom Emojis")
        emoji_label.setObjectName("funImportsCatLabel")
        main_layout.addWidget(emoji_label)

        upload_emoji_btn = QPushButton("+ Upload Emoji Image")
        upload_emoji_btn.setObjectName("funImportsCatBtn")
        upload_emoji_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        upload_emoji_btn.clicked.connect(self._upload_emoji)
        main_layout.addWidget(upload_emoji_btn)

        emoji_hint = QLabel("Uploaded images appear in the Emojis tab.")
        emoji_hint.setStyleSheet("color: #9CA3AF; font-size: 11px; padding: 2px 0;")
        main_layout.addWidget(emoji_hint)

        main_layout.addSpacing(16)

        gif_label = QLabel("Upload Custom GIFs")
        gif_label.setObjectName("funImportsCatLabel")
        main_layout.addWidget(gif_label)

        upload_gif_btn = QPushButton("+ Upload GIF")
        upload_gif_btn.setObjectName("funImportsCatBtn")
        upload_gif_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        upload_gif_btn.clicked.connect(self._upload_gif)
        main_layout.addWidget(upload_gif_btn)

        gif_hint = QLabel("Uploaded GIFs appear in the GIFs tab.")
        gif_hint.setStyleSheet("color: #9CA3AF; font-size: 11px; padding: 2px 0;")
        main_layout.addWidget(gif_hint)

        main_layout.addStretch()
        return widget

    def _insert_gif(self, gif):
        if self.target_edit:
            from PyQt6.QtCore import QUrl

            self.target_edit.insertHtml(
                f'<img src="{QUrl.fromLocalFile(gif).toString()}" '
                f'width="150" height="150" />'
            )
        self.accept()
