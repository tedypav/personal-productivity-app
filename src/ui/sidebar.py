from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QHBoxLayout, QInputDialog, QMessageBox, QMenu,
    QDialog, QListWidget, QDialogButtonBox, QLabel, QLineEdit, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from src.repositories.page_repo import PageRepo
from src.models.page import Page
from src.settings import load_settings
from src.undo_manager import undo_manager, capture_page_tree


class Sidebar(QWidget):
    page_selected = pyqtSignal(int)
    pages_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.repo = PageRepo()
        self.settings = load_settings()
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)
        self.setStyleSheet("""
            QTreeWidget {
                border: none;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 4px 2px;
            }
            QTreeWidget::item:selected {
                background-color: #e0e7ff;
                color: #1e40af;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #f8f9fa;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #e9ecef;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        btn_layout = QHBoxLayout()
        self.btn_new = QPushButton("+ New Page")
        self.btn_new_page = QPushButton("Bulk Time-Based")
        self.btn_bulk_named = QPushButton("+ Bulk Named")
        btn_layout.addWidget(self.btn_new)
        btn_layout.addWidget(self.btn_new_page)
        btn_layout.addWidget(self.btn_bulk_named)
        layout.addLayout(btn_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.setAnimated(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)

        self.btn_new.clicked.connect(self._create_page)
        self.btn_new_page.clicked.connect(self._bulk_creation_requested)
        self.btn_bulk_named.clicked.connect(self._bulk_named_dialog)

        self._load_pages()

    def _load_pages(self):
        self.tree.clear()
        pages = self.repo.get_all()
        root_pages = [p for p in pages if p.parent_id is None]

        def add_children(parent_item, parent_id):
            children = [p for p in pages if p.parent_id == parent_id]
            for page in sorted(children, key=lambda x: x.sort_order):
                item = QTreeWidgetItem(parent_item)
                item.setText(0, page.title)
                item.setData(0, Qt.ItemDataRole.UserRole, page.id)
                add_children(item, page.id)

        for page in sorted(root_pages, key=lambda x: x.sort_order):
            item = QTreeWidgetItem(self.tree)
            item.setText(0, page.title)
            item.setData(0, Qt.ItemDataRole.UserRole, page.id)
            add_children(item, page.id)

    def _on_item_clicked(self, item, column):
        page_id = item.data(0, Qt.ItemDataRole.UserRole)
        if page_id:
            self.page_selected.emit(page_id)

    def _create_page(self):
        title, ok = QInputDialog.getText(self, "New Page", "Page title:")
        if ok and title.strip():
            page = Page(title=title.strip())
            self.repo.create(page)
            self._load_pages()
            self.pages_changed.emit()

    def _bulk_creation_requested(self):
        self._bulk_create_dialog()

    def _bulk_create_dialog(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QDateEdit, QLabel, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle("Bulk Create Pages")
        layout = QVBoxLayout(dialog)

        mode_combo = QComboBox()
        mode_combo.addItems(["Days", "Weeks", "Years"])
        layout.addWidget(QLabel("Mode:"))
        layout.addWidget(mode_combo)

        start_date = QDateEdit()
        start_date.setCalendarPopup(True)
        start_date.setDate(QDate.currentDate())
        layout.addWidget(QLabel("Start date:"))
        layout.addWidget(start_date)

        end_label = QLabel("End date:")
        end_date = QDateEdit()
        end_date.setCalendarPopup(True)
        end_date.setDate(QDate.currentDate())
        layout.addWidget(end_label)
        layout.addWidget(end_date)

        week_start_label = QLabel("Week starts on:")
        week_start_combo = QComboBox()
        week_start_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
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

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            mode = mode_combo.currentText()
            from datetime import datetime, timedelta
            start = start_date.date().toPyDate()
            end = end_date.date().toPyDate()

            titles = []
            if mode == "Days":
                current = start
                while current <= end:
                    titles.append(current.strftime("%Y-%m-%d"))
                    current += timedelta(days=1)
            elif mode == "Weeks":
                week_days = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
                target_wd = week_days[week_start_combo.currentText()]
                current = start
                while current.weekday() != target_wd:
                    current -= timedelta(days=1)
                while current <= end:
                    week_end = current + timedelta(days=6)
                    titles.append(f"{current.strftime('%Y-%m-%d')} - {week_end.strftime('%Y-%m-%d')}")
                    current += timedelta(weeks=1)
            elif mode == "Years":
                for year in range(start.year, end.year + 1):
                    titles.append(str(year))

            for title in titles:
                self.repo.create(Page(title=title))
            self._load_pages()
            self.pages_changed.emit()

    def _bulk_named_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Bulk Create Named Pages")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Base name:"))
        name_edit = QLineEdit("Page")
        layout.addWidget(name_edit)

        layout.addWidget(QLabel("Number of pages:"))
        count_spin = QSpinBox()
        count_spin.setRange(1, 999)
        count_spin.setValue(5)
        layout.addWidget(count_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            base = name_edit.text().strip()
            count = count_spin.value()
            if not base:
                return
            for i in range(1, count + 1):
                self.repo.create(Page(title=f"{base} {i}"))
            self._load_pages()
            self.pages_changed.emit()

    def _show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return

        selected = self.tree.selectedItems()
        page_id = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu()

        if len(selected) > 1:
            delete_sel = menu.addAction(f"Delete Selected ({len(selected)})")
            template_sel = menu.addAction(f"Insert Template into Selected ({len(selected)})")
            action = menu.exec(self.tree.viewport().mapToGlobal(pos))
            if action == delete_sel:
                self._bulk_delete(selected)
            elif action == template_sel:
                self._bulk_insert_template(selected)
            return

        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        add_child_action = menu.addAction("Add Child Page")
        menu.addSeparator()
        move_up_action = menu.addAction("Move Up")
        move_down_action = menu.addAction("Move Down")

        action = menu.exec(self.tree.viewport().mapToGlobal(pos))

        if action == rename_action:
            current = item.text(0)
            title, ok = QInputDialog.getText(self, "Rename Page", "New title:", text=current)
            if ok and title.strip():
                page = self.repo.get_by_id(page_id)
                if page:
                    page.title = title.strip()
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
                page = Page(title=title.strip(), parent_id=page_id)
                self.repo.create(page)
                self._load_pages()
                self.pages_changed.emit()

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

        for pid in all_ids:
            self.repo.delete(pid)
        self._load_pages()
        self.pages_changed.emit()

    def _bulk_insert_template(self, items):
        from src.repositories.template_repo import TemplateRepo
        from src.repositories.block_repo import BlockRepo
        from src.models.content_block import ContentBlock
        import json

        repo = TemplateRepo()
        templates = repo.get_all()
        if not templates:
            QMessageBox.information(self, "Templates", "No templates saved yet.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Insert Template into Selected Pages")
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
            page_ids = [item.data(0, Qt.ItemDataRole.UserRole) for item in items if item.data(0, Qt.ItemDataRole.UserRole)]
            for pid in page_ids:
                for bd in blocks_data:
                    block = ContentBlock(
                        page_id=pid,
                        block_type=bd.get("block_type", "text"),
                        content_markdown=bd.get("content_markdown", "")
                    )
                    BlockRepo().create(block)
            QMessageBox.information(self, "Template", f"Template '{template.name}' inserted into {len(page_ids)} page(s).")

    def delete_selected(self):
        items = self.tree.selectedItems()
        if len(items) > 1:
            self._bulk_delete(items)

    def refresh(self):
        self._load_pages()
