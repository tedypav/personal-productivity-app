import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QHBoxLayout, QInputDialog, QMessageBox, QMenu,
    QDialog, QListWidget, QDialogButtonBox, QLabel, QLineEdit, QSpinBox,
    QAbstractItemView, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QMimeData, QSize
from PyQt6.QtGui import QKeySequence, QAction, QDrag, QIcon
from src.repositories.page_repo import PageRepo
from src.models.page import Page
from src.settings import load_settings
from src.undo_manager import undo_manager, capture_page_tree


def _get_icon_path(name):
    """Get path to an icon file."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons", f"{name}.svg")


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

            current_parent = page.parent_id
            target_parent = target_folder_id
            if current_parent == target_parent:
                continue
            if current_parent is None and target_parent is None:
                continue
            if current_parent is not None and target_parent is not None and int(current_parent) == int(target_parent):
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
            Sidebar {
                background: #FFF8F5;
            }
            QTreeWidget {
                background: #FFFFFF;
                border: 1px solid #F0E6E8;
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
                padding: 7px 14px;
                border: 1px solid #F0E6E8;
                border-radius: 18px;
                background: #FFFFFF;
                font-size: 11px;
                color: #2E2B2B;
            }
            QPushButton:hover {
                background: #FFF0F3;
                border-color: #F7D1DC;
            }
            QPushButton:pressed {
                background: #F7D1DC;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        btn_layout = QHBoxLayout()
        self.btn_new = QPushButton("+ New Page")
        self.btn_new_folder = QPushButton("+ Folder")
        self.btn_new_page = QPushButton("Bulk Time-Based")
        btn_layout.addWidget(self.btn_new)
        btn_layout.addWidget(self.btn_new_folder)
        btn_layout.addWidget(self.btn_new_page)
        layout.addLayout(btn_layout)

        btn_layout2 = QHBoxLayout()
        self.btn_bulk_named = QPushButton("+ Bulk Named")
        btn_layout2.addWidget(self.btn_bulk_named)
        btn_layout2.addStretch()
        layout.addLayout(btn_layout2)

        view_layout = QHBoxLayout()
        self.btn_expand = QPushButton("Show All")
        self.btn_collapse = QPushButton("Hide All")
        self.btn_expand.setStyleSheet("QPushButton { padding: 4px 10px; font-size: 10px; border-radius: 14px; }")
        self.btn_collapse.setStyleSheet("QPushButton { padding: 4px 10px; font-size: 10px; border-radius: 14px; }")
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
        self.tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.tree, 1)  # Stretch factor 1 to fill remaining space

        self.btn_expand.clicked.connect(self.tree.expandAll)
        self.btn_collapse.clicked.connect(self.tree.collapseAll)

        self.btn_new.clicked.connect(self._create_page)
        self.btn_new_folder.clicked.connect(self._create_folder)
        self.btn_new_page.clicked.connect(self._bulk_creation_requested)
        self.btn_bulk_named.clicked.connect(self._bulk_named_dialog)

        self._setup_shortcuts()
        self._load_pages()

    def _setup_shortcuts(self):
        delete_action = QAction("Delete", self.tree)
        delete_action.setShortcut(QKeySequence("Delete"))
        delete_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        delete_action.triggered.connect(self._delete_selected)
        self.tree.addAction(delete_action)

        rename_action = QAction("Rename", self.tree)
        rename_action.setShortcut(QKeySequence("F2"))
        rename_action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        rename_action.triggered.connect(self._rename_selected)
        self.tree.addAction(rename_action)

    def _load_pages(self):
        expanded_ids = self._collect_expanded()
        self.tree.clear()
        pages = self.repo.get_all()
        root_pages = [p for p in pages if p.parent_id is None]

        folder_icon = QIcon(_get_icon_path("folder"))
        page_icon = QIcon(_get_icon_path("page"))

        def add_children(parent_item, parent_id):
            children = [p for p in pages if p.parent_id == parent_id]
            for page in sorted(children, key=lambda x: x.sort_order):
                item = QTreeWidgetItem(parent_item)
                if page.page_type == "folder":
                    item.setIcon(0, folder_icon)
                    item.setText(0, page.title)
                    # Make folders bold
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)
                else:
                    item.setIcon(0, page_icon)
                    item.setText(0, page.title)
                item.setData(0, Qt.ItemDataRole.UserRole, page.id)
                item.setData(0, Qt.ItemDataRole.UserRole + 1, page.page_type)
                add_children(item, page.id)

        for page in sorted(root_pages, key=lambda x: x.sort_order):
            item = QTreeWidgetItem(self.tree)
            if page.page_type == "folder":
                item.setIcon(0, folder_icon)
                item.setText(0, page.title)
                # Make folders bold
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
            else:
                item.setIcon(0, page_icon)
                item.setText(0, page.title)
            item.setData(0, Qt.ItemDataRole.UserRole, page.id)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, page.page_type)
            add_children(item, page.id)

        if expanded_ids:
            self._restore_expanded(expanded_ids)
        else:
            self.tree.expandAll()

    def _collect_expanded(self):
        ids = set()
        root = self.tree.invisibleRootItem()
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

    def _restore_expanded(self, ids):
        root = self.tree.invisibleRootItem()
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

    def _create_page(self):
        title, ok = QInputDialog.getText(self, "New Page", "Page title:")
        if ok and title.strip():
            selected = self.tree.selectedItems()
            if selected:
                for item in selected:
                    parent_id = item.data(0, Qt.ItemDataRole.UserRole)
                    self.repo.create(Page(title=title.strip(), parent_id=parent_id, page_type="page"))
            else:
                self.repo.create(Page(title=title.strip(), page_type="page"))
            self._load_pages()
            self.pages_changed.emit()

    def _create_folder(self):
        title, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and title.strip():
            selected = self.tree.selectedItems()
            if selected:
                for item in selected:
                    parent_id = item.data(0, Qt.ItemDataRole.UserRole)
                    self.repo.create(Page(title=title.strip(), parent_id=parent_id, page_type="folder"))
            else:
                self.repo.create(Page(title=title.strip(), page_type="folder"))
            self._load_pages()
            self.pages_changed.emit()

    def _bulk_creation_requested(self):
        self._bulk_create_dialog()

    def _bulk_create_dialog(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QDateEdit, QLabel, QDialogButtonBox
        from PyQt6.QtGui import QIcon
        import os
        dialog = QDialog(self)
        dialog.setWindowTitle("Bulk Create Pages")
        
        # Title with logo
        title_layout = QHBoxLayout()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons", "logo_icon.svg")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_label.setPixmap(QIcon(logo_path).pixmap(28, 28))
            title_layout.addWidget(logo_label)
        title_label = QLabel("Bulk Create Pages")
        title_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #2E2B2B; font-family: 'Playfair Display', serif;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
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

        def _validate():
            mode = mode_combo.currentText()
            if mode == "Days" and end_date.date() <= start_date.date():
                end_date.setDate(start_date.date().addDays(1))
            elif mode == "Weeks" and end_date.date() < start_date.date().addDays(7):
                end_date.setDate(start_date.date().addDays(7))
            elif mode == "Years" and end_date.date() <= start_date.date().addYears(1):
                end_date.setDate(start_date.date().addYears(1))

        end_date.dateChanged.connect(_validate)

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
                self.repo.create(Page(title=title, page_type="page"))
            self._load_pages()
            self.pages_changed.emit()

    def _bulk_named_dialog(self):
        from PyQt6.QtGui import QIcon
        import os
        dialog = QDialog(self)
        dialog.setWindowTitle("Bulk Create Named Pages")
        
        # Title with logo
        title_layout = QHBoxLayout()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons", "logo_icon.svg")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_label.setPixmap(QIcon(logo_path).pixmap(28, 28))
            title_layout.addWidget(logo_label)
        title_label = QLabel("Bulk Create Named Pages")
        title_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #2E2B2B; font-family: 'Playfair Display', serif;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
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
                self.repo.create(Page(title=f"{base} {i}", page_type="page"))
            self._load_pages()
            self.pages_changed.emit()

    def _show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return

        selected = self.tree.selectedItems()
        page_id = item.data(0, Qt.ItemDataRole.UserRole)
        page_type = item.data(0, Qt.ItemDataRole.UserRole + 1) or "page"
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
        menu.addSeparator()
        add_child_action = menu.addAction("Add Child Page")
        add_folder_action = menu.addAction("Add Child Folder")
        menu.addSeparator()
        move_action = menu.addAction("Move to Folder...")
        menu.addSeparator()
        move_up_action = menu.addAction("Move Up")
        move_down_action = menu.addAction("Move Down")

        action = menu.exec(self.tree.viewport().mapToGlobal(pos))

        if action == rename_action:
            current = item.text(0)
            if page_type == "folder":
                current = current.replace("📁 ", "", 1)
            title, ok = QInputDialog.getText(self, "Rename", "New name:", text=current)
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

    def _move_to_folder(self, page_id, page_type):
        """Show dialog to move page/folder to another folder or root."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Move to Folder")
        dialog.setMinimumWidth(300)
        dialog.setMinimumHeight(400)
        
        # Title with logo
        title_layout = QHBoxLayout()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons", "logo_icon.svg")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_label.setPixmap(QIcon(logo_path).pixmap(28, 28))
            title_layout.addWidget(logo_label)
        title_label = QLabel("Move to Folder")
        title_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #2E2B2B; font-family: 'Playfair Display', serif;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
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
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
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
                        QMessageBox.warning(self, "Invalid Move", "Cannot move a folder into itself or its descendants.")
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
        
        # Title with logo
        title_layout = QHBoxLayout()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons", "logo_icon.svg")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_label.setPixmap(QIcon(logo_path).pixmap(28, 28))
            title_layout.addWidget(logo_label)
        title_label = QLabel("Insert Template into Selected Pages")
        title_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #2E2B2B; font-family: 'Playfair Display', serif;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout = QVBoxLayout(dialog)
        layout.addLayout(title_layout)
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
        items = self.tree.selectedItems()
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
