import sys

import pytest
from PyQt6.QtWidgets import QApplication

from src.database import init_db
from src.models.content_block import ContentBlock
from src.models.page import Page
from src.repositories.block_repo import BlockRepo
from src.repositories.page_repo import PageRepo


@pytest.fixture
def db_init():
    init_db()


@pytest.fixture
def app_instance():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestSidebarExtended:
    def test_sidebar_refresh(self, app_instance, db_init):
        from src.ui.sidebar import Sidebar

        s = Sidebar()
        PageRepo.create(Page(title="TestPage"))
        s.refresh()
        assert s.tree.topLevelItemCount() > 0
        s.close()

    def test_sidebar_expand_collapse(self, app_instance, db_init):
        from src.ui.sidebar import Sidebar

        s = Sidebar()
        PageRepo.create(Page(title="TestPage"))
        s.refresh()
        s._expand_all()
        s._collapse_all()
        s.close()

    def test_sidebar_template_tree(self, app_instance, db_init):
        from src.ui.sidebar import Sidebar

        s = Sidebar()
        assert s.template_tree is not None
        s.close()

    def test_sidebar_ensure_templates_folder(self, app_instance, db_init):
        from src.ui.sidebar import Sidebar

        s = Sidebar()
        s._ensure_templates_folder()
        s.close()

    def test_sidebar_ensure_archive_folder(self, app_instance, db_init):
        from src.ui.sidebar import Sidebar

        s = Sidebar()
        s._ensure_archive_folder()
        s.close()

    def test_sidebar_ensure_fun_imports_folder(self, app_instance, db_init):
        from src.ui.sidebar import Sidebar

        s = Sidebar()
        s._ensure_fun_imports_folder()
        s.close()


class TestMainWindowExtended:
    def test_main_window_undo_delete_empty(self, app_instance, db_init):
        from src.ui.main_window import MainWindow
        from src.undo_manager import undo_manager

        undo_manager._actions.clear()
        mw = MainWindow()
        mw._undo_delete()
        mw.close()

    def test_main_window_bulk_delete(self, app_instance, db_init):
        from src.ui.main_window import MainWindow

        mw = MainWindow()
        mw._bulk_delete_selected()
        mw.close()


class TestEditorExtended2:
    def test_editor_embedded_task_list(self, app_instance, db_init):
        from src.ui.editor import PageEditor

        e = PageEditor()
        pid = PageRepo.create(Page(title="Test"))
        BlockRepo.create(
            ContentBlock(
                page_id=pid,
                block_type="text",
                content_markdown="<p>Hello</p>",
            )
        )
        e.load_page(pid)
        if e._block_widgets:
            block_w = e._block_widgets[0]
            has_body = hasattr(block_w, "_body_widget")
            has_task = has_body and hasattr(block_w._body_widget, "add_task_list")
            if has_task:
                block_w._body_widget.add_task_list()
        e.close()

    def test_editor_table_widget_creation(self, app_instance, db_init):
        from src.ui.editor import PageEditor

        e = PageEditor()
        pid = PageRepo.create(Page(title="Test"))
        e.load_page(pid)
        e._add_block("table")
        assert len(e._block_widgets) == 1
        e.close()

    def test_editor_list_block_creation(self, app_instance, db_init):
        from src.ui.editor import PageEditor

        e = PageEditor()
        pid = PageRepo.create(Page(title="Test"))
        e.load_page(pid)
        e._add_block("checkbox")
        assert len(e._block_widgets) == 1
        e.close()

    def test_editor_on_add_list_no_focus(self, app_instance, db_init):
        from src.ui.editor import PageEditor

        e = PageEditor()
        pid = PageRepo.create(Page(title="Test"))
        e.load_page(pid)
        e._on_add_list()
        e.close()

    def test_editor_clear_selection(self, app_instance, db_init):
        from src.ui.editor import PageEditor

        e = PageEditor()
        pid = PageRepo.create(Page(title="Test"))
        e.load_page(pid)
        e._clear_selection()
        e.close()

    def test_editor_scroll_to_newest(self, app_instance, db_init):
        from src.ui.editor import PageEditor

        e = PageEditor()
        pid = PageRepo.create(Page(title="Test"))
        e.load_page(pid)
        e._scroll_to_newest_block()
        e.close()

    def test_editor_find_block_widget(self, app_instance, db_init):
        from src.ui.editor import PageEditor

        e = PageEditor()
        result = PageEditor._find_block_widget(e)
        assert result is None
        e.close()

    def test_editor_find_nearest_table_cell(self, app_instance, db_init):
        from src.ui.editor import PageEditor

        e = PageEditor()
        result = PageEditor._find_nearest_table_cell(e)
        assert result is None
        e.close()

    def test_editor_get_active_text_edit(self, app_instance, db_init):
        from src.ui.editor import PageEditor

        e = PageEditor()
        result = e._get_active_text_edit()
        assert result is None or isinstance(result, tuple)
        e.close()

    def test_editor_on_focus_changed(self, app_instance, db_init):
        from src.ui.editor import PageEditor

        e = PageEditor()
        e._on_focus_changed(None, e)
        e.close()


class TestContentBlockWidgetExtended:
    def test_block_header_editable(self, app_instance, db_init):
        from src.ui.editor import ContentBlockWidget

        pid = PageRepo.create(Page(title="Test"))
        BlockRepo.create(
            ContentBlock(
                page_id=pid,
                block_type="text",
                content_markdown="Hello",
            )
        )
        block = BlockRepo.get_by_page(pid)[0]
        cbw = ContentBlockWidget(block=block)
        assert cbw._header_edit is not None
        cbw.close()

    def test_block_alignment_buttons(self, app_instance, db_init):
        from src.ui.editor import ContentBlockWidget

        pid = PageRepo.create(Page(title="Test"))
        BlockRepo.create(
            ContentBlock(
                page_id=pid,
                block_type="text",
                content_markdown="Hello",
            )
        )
        block = BlockRepo.get_by_page(pid)[0]
        cbw = ContentBlockWidget(block=block)
        assert cbw._h_left_btn is not None
        assert cbw._h_align_group is not None
        cbw.close()

    def test_block_delete_button(self, app_instance, db_init):
        from src.ui.editor import ContentBlockWidget

        pid = PageRepo.create(Page(title="Test"))
        BlockRepo.create(
            ContentBlock(
                page_id=pid,
                block_type="text",
                content_markdown="Hello",
            )
        )
        block = BlockRepo.get_by_page(pid)[0]
        cbw = ContentBlockWidget(block=block)
        assert hasattr(cbw, "delete_requested")
        cbw.close()

    def test_block_drag_handle(self, app_instance, db_init):
        from src.ui.editor import ContentBlockWidget

        pid = PageRepo.create(Page(title="Test"))
        BlockRepo.create(
            ContentBlock(
                page_id=pid,
                block_type="text",
                content_markdown="Hello",
            )
        )
        block = BlockRepo.get_by_page(pid)[0]
        cbw = ContentBlockWidget(block=block)
        assert cbw.drag_handle is not None
        cbw.close()
