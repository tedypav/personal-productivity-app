from PyQt6.QtCore import QEvent, QMimeData, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStyledItemDelegate,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.models.page import Page
from src.repositories.page_object_repo import PageObjectRepo
from src.repositories.page_repo import PageRepo
from src.settings import load_settings
from src.ui.dialogs import _get_icon_path, create_dialog_header
from src.ui.fun_imports import FunImportsDialog
from src.undo_manager import capture_page_tree, undo_manager


class DeleteButtonDelegate(QStyledItemDelegate):
    def __init__(self, tree, sidebar):
        super().__init__(tree)
        self._tree = tree
        self._sidebar = sidebar
        self._hovered_index = None
        tree.setMouseTracking(True)
        tree.viewport().installEventFilter(self)
        tree.model().rowsRemoved.connect(self._on_rows_removed)
        tree.model().modelReset.connect(self._on_model_reset)

    def _on_model_reset(self):
        self._hovered_index = None

    def _on_rows_removed(self, parent, first, last):
        if self._hovered_index and self._hovered_index.parent() == parent:
            row = self._hovered_index.row()
            if first <= row <= last:
                self._hovered_index = None

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        can_delete = index.data(Qt.ItemDataRole.UserRole + 2)
        if not can_delete:
            return

        btn_rect = self._get_button_rect(option.rect)
        is_hovered = self._hovered_index == index

        painter.save()
        if is_hovered:
            painter.setPen(QColor("#EF4444"))
        else:
            painter.setPen(QColor("#9CA3AF"))
        font = QFont("Inter", 12)
        painter.setFont(font)
        painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "\u00d7")
        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseMove:
            item = self._tree.itemAt(event.position().toPoint())
            new_index = self._tree.indexFromItem(item) if item else None
            if new_index != self._hovered_index:
                old = self._hovered_index
                self._hovered_index = new_index
                if old and old.isValid():
                    old_item = self._tree.itemFromIndex(old)
                    if old_item:
                        self._tree.viewport().update(
                            self._tree.visualItemRect(old_item)
                        )
                if new_index and new_index.isValid():
                    self._tree.viewport().update(self._tree.visualItemRect(item))
        elif event.type() == QEvent.Type.MouseButtonPress:
            can_delete = index.data(Qt.ItemDataRole.UserRole + 2)
            if can_delete:
                btn_rect = self._get_button_rect(option.rect)
                if btn_rect.contains(event.position().toPoint()):
                    page_id = index.data(Qt.ItemDataRole.UserRole)
                    self._sidebar._delete_item(page_id)
                    return True
        elif event.type() == QEvent.Type.Leave:
            old = self._hovered_index
            self._hovered_index = None
            if old and old.isValid():
                old_item = self._tree.itemFromIndex(old)
                if old_item:
                    self._tree.viewport().update(self._tree.visualItemRect(old_item))
        return super().editorEvent(event, model, option, index)

    def _get_button_rect(self, item_rect):
        btn_size = 18
        return QRect(
            item_rect.right() - btn_size - 6,
            item_rect.top() + (item_rect.height() - btn_size) // 2,
            btn_size,
            btn_size,
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

        self._build_buttons(layout)
        self._build_trees(layout)

        self._setup_shortcuts()
        self._ensure_special_folders()
        self._editor_ref = None
        self._load_pages()

    def _build_buttons(self, layout):
        page_icon = QIcon(_get_icon_path("page"))
        folder_icon = QIcon(_get_icon_path("folder"))
        archive_icon = QIcon(_get_icon_path("folder_archive"))
        template_icon = QIcon(_get_icon_path("page_template"))

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(3)

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
        self.btn_archive = QPushButton("Archive")
        self.btn_archive.setIcon(archive_icon)
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

        self.btn_new.clicked.connect(self._create_page)
        self.btn_new_folder.clicked.connect(self._create_folder)
        self.btn_new_page.clicked.connect(self._bulk_creation_requested)
        self.btn_bulk_named.clicked.connect(self._bulk_named_dialog)
        self.btn_archive.clicked.connect(self._archive_selected)
        self.btn_template.clicked.connect(self._template_clicked)
        self.btn_expand.clicked.connect(self._expand_all)
        self.btn_collapse.clicked.connect(self._collapse_all)

    def _build_trees(self, layout):
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

        self._tree_delegate = DeleteButtonDelegate(self.tree, self)
        self.tree.setItemDelegate(self._tree_delegate)
        self._template_delegate = DeleteButtonDelegate(self.template_tree, self)
        self.template_tree.setItemDelegate(self._template_delegate)

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

        special_titles = {"Fun Imports", "Archive", "Templates"}

        def _make_item(parent, page, tree):
            item = QTreeWidgetItem(parent)
            item.setIcon(0, _page_icon(page))
            item.setText(0, page.title)
            if page.page_type == "folder":
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
            item.setData(0, Qt.ItemDataRole.UserRole, page.id)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, page.page_type)
            is_system_folder = (
                tree is self.template_tree
                and page.page_type == "folder"
                and page.title in special_titles
            )
            item.setData(0, Qt.ItemDataRole.UserRole + 2, not is_system_folder)
            return item

        def add_children(parent_item, parent_id, tree):
            children = children_map.get(parent_id, [])
            for page in sorted(children, key=lambda x: x.title.lower()):
                _make_item(parent_item, page, tree)
                child_item = parent_item.child(parent_item.childCount() - 1)
                add_children(child_item, page.id, tree)

        # Separate special folders from regular pages
        special_root = [
            p
            for p in root_pages
            if p.title in special_titles and p.page_type == "folder"
        ]
        regular_root = [p for p in root_pages if p.title not in special_titles]

        # Upper tree: regular pages/folders
        for page in sorted(regular_root, key=lambda x: x.title.lower()):
            item = _make_item(self.tree, page, self.tree)
            add_children(item, page.id, self.tree)

        # Lower tree: special folders
        for page in sorted(special_root, key=lambda x: x.title.lower()):
            item = _make_item(self.template_tree, page, self.template_tree)
            add_children(item, page.id, self.template_tree)

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
        page_id = item.data(0, Qt.ItemDataRole.UserRole)
        page_title = item.text(0)
        if page_title == "Fun Imports":
            self._open_fun_imports()
        elif page_id:
            self.page_selected.emit(page_id)

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
        from src.ui.bulk_create_dialog import BulkCreateDialog

        selected_folder_id = None
        selected = self.tree.selectedItems()
        if selected:
            selected_folder_id = selected[0].data(0, Qt.ItemDataRole.UserRole)

        dialog = BulkCreateDialog(self, self.settings, selected_folder_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            titles = dialog.get_titles()
            existing = {p.title for p in self.repo.get_children(selected_folder_id)}
            for title in titles:
                if title not in existing:
                    self.repo.create(
                        Page(
                            title=title,
                            page_type="page",
                            parent_id=selected_folder_id,
                        )
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
        count_spin.setStyleSheet("""
            QSpinBox {
                padding: 6px 12px;
                border: 1px solid #F7D1DC;
                border-radius: 10px;
                background: #FFFFFF;
                font-size: 13px;
                color: #2E2B2B;
                min-width: 120px;
                font-family: 'Inter', 'Poppins', sans-serif;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                width: 22px;
                border-radius: 11px;
                background: #FFF0F3;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #FFE4EC;
            }
            QSpinBox::up-arrow {
                image: url(assets/icons/chevron_up.svg);
                width: 10px;
                height: 10px;
            }
            QSpinBox::down-arrow {
                image: url(assets/icons/chevron_down.svg);
                width: 10px;
                height: 10px;
            }
        """)
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
            existing = {p.title for p in self.repo.get_children(selected_folder_id)}
            for i in range(1, count + 1):
                title = f"{base} {i}"
                if title not in existing:
                    self.repo.create(
                        Page(
                            title=title,
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

        handlers = {
            rename_action: lambda: self._ctx_rename(item, page_id, page_type),
            delete_action: lambda: self._ctx_delete(page_id),
            add_child_action: lambda: self._ctx_add_child(page_id),
            move_action: lambda: self._move_to_folder(page_id, page_type),
            move_up_action: lambda: self._ctx_move(page_id, -1),
            move_down_action: lambda: self._ctx_move(page_id, 1),
            archive_action: lambda: self._ctx_archive(page_id, page_type),
            set_template_action: lambda: self._set_as_template(page_id),
        }
        if add_folder_action:
            handlers[add_folder_action] = lambda: self._ctx_add_child(page_id, "folder")

        handler = handlers.get(action)
        if handler:
            handler()

    def _ctx_rename(self, item, page_id, page_type):
        current = item.text(0)
        if page_type == "folder":
            current = current.replace("\U0001f4c1 ", "", 1)
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

    def _ctx_delete(self, page_id):
        data = capture_page_tree(page_id)
        if data:
            data["type"] = "page"
            undo_manager.push(data)
        self.repo.delete(page_id)
        self._load_pages()
        self.pages_changed.emit()

    def _ctx_add_child(self, page_id, page_type="page"):
        label = "Folder name:" if page_type == "folder" else "Page title:"
        title, ok = QInputDialog.getText(self, "New Child", label)
        if ok and title.strip():
            page = Page(title=title.strip(), parent_id=page_id, page_type=page_type)
            self.repo.create(page)
            self._load_pages()
            self.pages_changed.emit()

    def _ctx_move(self, page_id, direction):
        page = self.repo.get_by_id(page_id)
        if page:
            page.sort_order = max(0, page.sort_order + direction)
            self.repo.update(page)
            self._load_pages()
            self.pages_changed.emit()

    def _ctx_archive(self, page_id, page_type):
        page = self.repo.get_by_id(page_id)
        if page and page.title in ("Archive", "Templates", "Fun Imports"):
            QMessageBox.information(
                self, "Archive", f"Cannot archive the {page.title} folder."
            )
        else:
            self._archive_item(page_id, page_type)

    def _find_or_create_archive(self):
        pages = self.repo.get_all()
        archive_folder = [
            p for p in pages if p.title == "Archive" and p.page_type == "folder"
        ]
        if archive_folder:
            return archive_folder[0].id, pages
        return self.repo.create(Page(title="Archive", page_type="folder")), pages

    def _archive_item(self, page_id, page_type):
        archive_id, pages = self._find_or_create_archive()

        if page_type == "folder":
            self._archive_folder(page_id, archive_id, pages)
        else:
            self._archive_page(page_id, archive_id, pages)

    def _archive_folder(self, page_id, archive_id, pages):
        page = self.repo.get_by_id(page_id)
        if not page:
            return
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
            for child in self.repo.get_children(page_id):
                child.parent_id = target_id
                self.repo.update(child)
            self.repo.delete(page_id)
        else:
            page.parent_id = archive_id
            self.repo.update(page)

    def _archive_page(self, page_id, archive_id, pages):
        page = self.repo.get_by_id(page_id)
        if not page:
            return
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
                target_folder_id = (
                    existing[0].id
                    if existing
                    else self.repo.create(
                        Page(
                            title=parent_page.title,
                            parent_id=archive_id,
                            page_type="folder",
                        )
                    )
                )
                page.title = self._get_unique_name(
                    page.title, target_folder_id, exclude_id=page_id
                )
                page.parent_id = target_folder_id
                self.repo.update(page)
        else:
            page.title = self._get_unique_name(
                page.title, archive_id, exclude_id=page_id
            )
            page.parent_id = archive_id
            self.repo.update(page)

        self._load_pages()
        if self._editor_ref and self._editor_ref.current_page_id == page_id:
            self._editor_ref.clear_editor()
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
        new_page_id = self.repo.create(new_page)
        PageObjectRepo.copy_objects(page_id, new_page_id)
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
        self._delete_items(
            self.tree.selectedItems() + self.template_tree.selectedItems()
        )

    def _delete_item(self, page_id):
        self._delete_items_by_id([page_id], clear_editor=True)

    def _delete_selected(self):
        self._delete_items(
            self.tree.selectedItems() + self.template_tree.selectedItems(),
            clear_editor=True,
        )

    def _delete_items(self, items, clear_editor=False):
        if not items:
            return
        if len(items) > 1:
            self._bulk_delete(items)
            return
        page_id = items[0].data(0, Qt.ItemDataRole.UserRole)
        self._delete_items_by_id([page_id], clear_editor=clear_editor)

    def _delete_items_by_id(self, page_ids, clear_editor=False):
        for page_id in page_ids:
            data = capture_page_tree(page_id)
            if data:
                data["type"] = "page"
                undo_manager.push(data)
            self.repo.delete(page_id)
            if clear_editor and self._editor_ref:
                if self._editor_ref.current_page_id == page_id:
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
