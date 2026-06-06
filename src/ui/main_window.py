import json

from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QInputDialog, QMessageBox,
    QMenuBar, QMenu, QDialog, QVBoxLayout, QLabel,
    QComboBox, QSpinBox, QDialogButtonBox, QWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence

from src.ui.sidebar import Sidebar
from src.ui.editor import PageEditor
from src.repositories.block_repo import BlockRepo
from src.repositories.template_repo import TemplateRepo
from src.models.template import Template
from src.database import init_db
from src.settings import load_settings, save_settings
from src.undo_manager import undo_manager, capture_page_tree


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        init_db()
        self.settings = load_settings()

        self.setWindowTitle("Personal Productivity App")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.sidebar = Sidebar()
        self.editor = PageEditor()

        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.editor)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([self.settings.get("sidebar_width", 250), 750])

        self.setCentralWidget(splitter)

        self.sidebar.page_selected.connect(self.editor.load_page)

        self._setup_menu()
        self._setup_shortcuts()

        undo_z = QAction("Undo Delete", self.sidebar)
        undo_z.setShortcut(QKeySequence("Ctrl+Z"))
        undo_z.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        undo_z.triggered.connect(self._undo_delete)
        self.sidebar.addAction(undo_z)

        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setInterval(self.settings.get("auto_save_interval_ms", 1000))
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._auto_save_timer.start()

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
        self._make_action(file_menu, "Save", self.editor.save_current, QKeySequence("Ctrl+S"))
        file_menu.addSeparator()
        self._make_action(file_menu, "Settings...", self._show_settings)
        file_menu.addSeparator()
        self._make_action(file_menu, "Exit", self.close, QKeySequence("Ctrl+Q"))

        page_menu = menubar.addMenu("Page")
        self._make_action(page_menu, "New Page", self._new_page)
        self._make_action(page_menu, "New Child Page", self._new_child_page)
        self._make_action(page_menu, "Save Page as Template", self._save_as_template)
        self._make_action(page_menu, "Delete Current Page", self._delete_page, QKeySequence("Delete"))
        page_menu.addSeparator()
        self._make_action(page_menu, "Bulk Create Pages", self._bulk_create)

        edit_menu = menubar.addMenu("Edit")
        self._undo_action = self._make_action(edit_menu, "Undo Delete", self._undo_delete, QKeySequence("Ctrl+Shift+Z"))
        edit_menu.addSeparator()
        self._make_action(edit_menu, "Delete Selected", self._bulk_delete_selected, QKeySequence("Ctrl+D"))
        self._make_action(edit_menu, "Bulk Create Pages", self._bulk_create, QKeySequence("Ctrl+Shift+B"))

        view_menu = menubar.addMenu("View")
        self._toggle_sidebar_action = self._make_action(view_menu, "Toggle Sidebar", self._toggle_sidebar)

    def _setup_shortcuts(self):
        new_child = QAction("New Child Page", self)
        new_child.setShortcut(QKeySequence("Ctrl+Shift+N"))
        new_child.triggered.connect(self._new_child_page)
        self.addAction(new_child)

        bold = QAction("Bold", self)
        bold.setShortcut(QKeySequence("Ctrl+B"))
        bold.triggered.connect(lambda: self._apply_to_text("bold"))
        self.addAction(bold)

        italic = QAction("Italic", self)
        italic.setShortcut(QKeySequence("Ctrl+I"))
        italic.triggered.connect(lambda: self._apply_to_text("italic"))
        self.addAction(italic)

        undo_u = QAction("Undo Delete", self)
        undo_u.setShortcut(QKeySequence("Ctrl+U"))
        undo_u.triggered.connect(self._undo_delete)
        self.addAction(undo_u)

    def _apply_to_text(self, fmt):
        if hasattr(self.editor, '_apply_format'):
            self.editor._apply_format(fmt)

    def _auto_save(self):
        self.editor.save_current()

    def _new_page(self):
        self.sidebar._create_page()

    def _new_child_page(self):
        from src.repositories.page_repo import PageRepo
        if self.editor.current_page_id:
            title, ok = QInputDialog.getText(self, "New Child Page", "Page title:")
            if ok and title.strip():
                from src.models.page import Page
                PageRepo().create(Page(title=title.strip(), parent_id=self.editor.current_page_id))
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
        self.editor.current_page_id = None
        self.editor.page_title.setText("Select a page")

    def _undo_delete(self):
        action = undo_manager.pop()
        if not action:
            return
        self.sidebar.refresh()
        if action["type"] == "page":
            self.editor.current_page_id = None
            self.editor.page_title.setText("Select a page")
        elif self.editor.current_page_id:
            self.editor.load_page(self.editor.current_page_id)

    def _bulk_delete_selected(self):
        self.sidebar.delete_selected()
        if not self.sidebar.tree.selectedItems():
            self.editor.current_page_id = None
            self.editor.page_title.setText("Select a page")

    def _save_as_template(self):
        if not self.editor.current_page_id:
            QMessageBox.information(self, "Template", "Select a page first.")
            return
        name, ok = QInputDialog.getText(self, "Save Template", "Template name:")
        if ok and name.strip():
            blocks = BlockRepo().get_by_page(self.editor.current_page_id)
            data = [{"block_type": b.block_type, "content_markdown": b.content_markdown} for b in blocks]
            template = Template(name=name.strip(), content_json=json.dumps(data))
            TemplateRepo().create(template)
            QMessageBox.information(self, "Template", f"Template '{name}' saved.")

    def _bulk_create(self):
        self.sidebar._bulk_create_dialog()

    def _toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def _show_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Week starts on:"))
        week_combo = QComboBox()
        week_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
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

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings["week_start_day"] = week_combo.currentText()
            self.settings["auto_save_interval_ms"] = interval_spin.value()
            self.settings["font_size"] = font_spin.value()
            save_settings(self.settings)
            self._auto_save_timer.setInterval(self.settings["auto_save_interval_ms"])
            QMessageBox.information(self, "Settings", "Settings saved. Restart to apply font size changes.")
