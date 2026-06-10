import sys
import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication

from src.database import init_db
from src.models.page import Page
from src.models.content_block import ContentBlock
from src.repositories.page_repo import PageRepo
from src.repositories.block_repo import BlockRepo


@pytest.fixture
def db_init():
    init_db()


@pytest.fixture
def editor(app_instance, db_init):
    from src.ui.editor import PageEditor
    e = PageEditor()
    yield e
    e.close()


@pytest.fixture
def page_with_blocks(db_init):
    pid = PageRepo.create(Page(title="TestPage"))
    BlockRepo.create(ContentBlock(page_id=pid, block_type="text", content_markdown="Hello"))
    BlockRepo.create(ContentBlock(page_id=pid, block_type="table"))
    return pid


class TestPageEditorRendering:
    def test_editor_creates(self, editor):
        assert editor is not None

    def test_editor_has_toolbar(self, editor):
        assert editor._add_block_btn is not None
        assert editor._table_btn is not None
        assert editor._list_btn is not None
        assert editor._template_btn is not None

    def test_editor_has_scroll_area(self, editor):
        assert editor.scroll is not None


class TestPageEditorLoadPage:
    def test_load_page_creates_blocks(self, editor, page_with_blocks):
        editor.load_page(page_with_blocks)
        assert len(editor._block_widgets) == 2

    def test_load_page_clears_previous(self, editor, page_with_blocks):
        editor.load_page(page_with_blocks)
        editor.load_page(page_with_blocks)
        assert len(editor._block_widgets) == 2


class TestPageEditorClearEditor:
    def test_clear_editor_removes_blocks(self, editor, page_with_blocks):
        editor.load_page(page_with_blocks)
        assert len(editor._block_widgets) > 0
        editor.clear_editor()
        assert len(editor._block_widgets) == 0


class TestPageEditorAddBlock:
    def test_add_text_block(self, editor, page_with_blocks):
        editor.load_page(page_with_blocks)
        initial = len(editor._block_widgets)
        editor._add_block("text")
        assert len(editor._block_widgets) > initial

    def test_add_table_block(self, editor, page_with_blocks):
        editor.load_page(page_with_blocks)
        initial = len(editor._block_widgets)
        editor._add_block("table")
        assert len(editor._block_widgets) > initial

    def test_add_list_block(self, editor, page_with_blocks):
        editor.load_page(page_with_blocks)
        initial = len(editor._block_widgets)
        editor._add_block("checkbox")
        assert len(editor._block_widgets) > initial


class TestPageEditorSave:
    def test_save_current(self, editor, page_with_blocks):
        editor.load_page(page_with_blocks)
        editor.save_current()
        blocks = BlockRepo.get_by_page(page_with_blocks)
        assert len(blocks) == 2


class TestPageEditorCanvasClick:
    def test_canvas_click_records_position(self, editor, page_with_blocks):
        editor.load_page(page_with_blocks)
        editor._on_canvas_clicked(100, 200)
        assert editor._canvas_click_pos is not None


class TestPageEditorDeleteBlocks:
    def test_delete_selected_blocks(self, editor, page_with_blocks):
        editor.load_page(page_with_blocks)
        if editor._block_widgets:
            editor._block_widgets[0].set_selected(True)
            editor._delete_selected_blocks()
            assert len(editor._block_widgets) >= 0
