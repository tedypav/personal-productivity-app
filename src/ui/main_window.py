import os

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
)

from src.database import init_db
from src.settings import load_settings, save_settings
from src.ui.dialogs import create_dialog_header
from src.ui.editor import PageEditor
from src.ui.sidebar import Sidebar
from src.undo_manager import capture_page_tree, undo_manager


def get_logo_path():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "assets",
        "icons",
        "logo_icon.ico",
    )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        init_db()
        self.settings = load_settings()

        self.setWindowTitle("Personal Productivity App")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        logo_path = get_logo_path()
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(6)

        self.sidebar = Sidebar()
        self.editor = PageEditor()

        self._splitter.addWidget(self.sidebar)
        self._splitter.addWidget(self.editor)
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 3)

        saved_sizes = self.settings.get("main_splitter_sizes")
        if saved_sizes:
            self._splitter.setSizes(saved_sizes)

        self._splitter.splitterMoved.connect(self._save_splitter_sizes)

        self.setCentralWidget(self._splitter)

        self.sidebar.page_selected.connect(self.editor.load_page)
        self.editor.navigate_to_page.connect(self._navigate_to_page)
        self.sidebar.set_editor(self.editor)
        self.sidebar.pages_changed.connect(self.editor.refresh_title)

        self._setup_menu()
        self._setup_shortcuts()

        undo_z = QAction("Undo Delete", self.sidebar)
        undo_z.setShortcut(QKeySequence("Ctrl+Z"))
        undo_z.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        undo_z.triggered.connect(self._undo_delete)
        self.sidebar.addAction(undo_z)

        QTimer.singleShot(0, self.showMaximized)

    def _make_action(self, menu, text, slot, shortcut=None):
        action = QAction(text, self)
        if slot:
            action.triggered.connect(slot)
        if shortcut:
            action.setShortcut(shortcut)
        menu.addAction(action)
        return action

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        self._make_action(file_menu, "New Page", self._new_page, QKeySequence("Ctrl+N"))
        file_menu.addSeparator()
        self._make_action(file_menu, "Settings...", self._show_settings)
        file_menu.addSeparator()
        self._make_action(file_menu, "Exit", self.close, QKeySequence("Ctrl+Q"))

        page_menu = menubar.addMenu("Page")
        self._make_action(page_menu, "New Page", self._new_page)
        self._make_action(page_menu, "New Child Page", self._new_child_page)
        self._make_action(page_menu, "Delete Current Page", self._delete_page)
        page_menu.addSeparator()
        self._make_action(page_menu, "Bulk Create Pages", self._bulk_create)

        edit_menu = menubar.addMenu("Edit")
        self._undo_action = self._make_action(
            edit_menu, "Undo Delete", self._undo_delete, QKeySequence("Ctrl+Shift+Z")
        )
        edit_menu.addSeparator()
        self._make_action(
            edit_menu,
            "Delete Selected",
            self._bulk_delete_selected,
        )
        self._make_action(
            edit_menu,
            "Bulk Create Pages",
            self._bulk_create,
            QKeySequence("Ctrl+Shift+B"),
        )

        view_menu = menubar.addMenu("View")
        self._toggle_sidebar_action = self._make_action(
            view_menu, "Toggle Sidebar", self._toggle_sidebar
        )

    def _setup_shortcuts(self):
        new_child = QAction("New Child Page", self)
        new_child.setShortcut(QKeySequence("Ctrl+Shift+N"))
        new_child.triggered.connect(self._new_child_page)
        self.addAction(new_child)

        undo_u = QAction("Undo Delete", self)
        undo_u.setShortcut(QKeySequence("Ctrl+U"))
        undo_u.triggered.connect(self._undo_delete)
        self.addAction(undo_u)

    def _save_splitter_sizes(self, pos, index):
        self.settings["main_splitter_sizes"] = self._splitter.sizes()
        save_settings(self.settings)

    def _navigate_to_page(self, page_id):
        from PyQt6.QtCore import Qt

        tree = self.sidebar.tree
        root = tree.invisibleRootItem()
        stack = [root]
        while stack:
            parent = stack.pop()
            for i in range(parent.childCount()):
                child = parent.child(i)
                pid = child.data(0, Qt.ItemDataRole.UserRole)
                if pid == page_id:
                    tree.setCurrentItem(child)
                    self.sidebar.page_selected.emit(page_id)
                    return
                stack.append(child)

    def _new_page(self):
        self.sidebar._create_page()

    def _new_child_page(self):
        from src.repositories.page_repo import PageRepo

        if self.editor.current_page_id:
            title, ok = QInputDialog.getText(self, "New Child Page", "Page title:")
            if ok and title.strip():
                from src.models.page import Page

                PageRepo().create(
                    Page(title=title.strip(), parent_id=self.editor.current_page_id)
                )
                self.sidebar.refresh()

    def _delete_page(self):
        selected = self.sidebar.tree.selectedItems()
        if len(selected) > 1:
            self._bulk_delete_selected()
            return
        if not self.editor.current_page_id:
            return
        from src.repositories.page_repo import PageRepo

        page_id = self.editor.current_page_id
        data = capture_page_tree(page_id)
        if data:
            data["type"] = "page"
            undo_manager.push(data)
        PageRepo().delete(page_id)
        self.sidebar.refresh()
        self.editor.clear_editor()

    def _undo_delete(self):
        action = undo_manager.pop()
        if not action:
            return
        self.sidebar.refresh()
        if action["type"] == "page":
            self.editor.clear_editor()
        elif self.editor.current_page_id:
            self.editor.load_page(self.editor.current_page_id)

    def _bulk_delete_selected(self):
        self.sidebar.delete_selected()
        if not self.sidebar.tree.selectedItems():
            self.editor.clear_editor()

    def _bulk_create(self):
        self.sidebar._bulk_create_dialog()

    def _toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def _show_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")

        title_layout = create_dialog_header("Settings")

        layout = QVBoxLayout(dialog)
        layout.addLayout(title_layout)

        layout.addWidget(QLabel("Week starts on:"))
        week_combo = QComboBox()
        week_combo.addItems(
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
        week_combo.setCurrentText(self.settings.get("week_start_day", "Monday"))
        layout.addWidget(week_combo)

        layout.addWidget(QLabel("Auto-save interval (ms):"))
        interval_spin = QSpinBox()
        interval_spin.setRange(500, 10000)
        interval_spin.setSingleStep(500)
        interval_spin.setValue(self.settings.get("auto_save_interval_ms", 1000))
        layout.addWidget(interval_spin)

        layout.addWidget(QLabel("Font size:"))
        font_spin = QSpinBox()
        font_spin.setRange(10, 32)
        font_spin.setValue(self.settings.get("font_size", 14))
        layout.addWidget(font_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings["week_start_day"] = week_combo.currentText()
            self.settings["auto_save_interval_ms"] = interval_spin.value()
            self.settings["font_size"] = font_spin.value()
            save_settings(self.settings)
            self._auto_save_timer.setInterval(self.settings["auto_save_interval_ms"])
            QMessageBox.information(
                self, "Settings", "Settings saved. Restart to apply font size changes."
            )
