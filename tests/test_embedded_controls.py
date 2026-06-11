import sys

import pytest
from PyQt6.QtWidgets import QApplication

from src.database import init_db


@pytest.fixture
def db_init():
    init_db()


@pytest.fixture
def app_instance():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def text_block(app_instance, db_init):
    from src.models.content_block import ContentBlock
    from src.models.page import Page
    from src.repositories.block_repo import BlockRepo
    from src.repositories.page_repo import PageRepo
    from src.ui.editor import ContentBlockWidget

    pid = PageRepo.create(Page(title="Test"))
    BlockRepo.create(
        ContentBlock(page_id=pid, block_type="text", content_markdown="Hello")
    )
    block = BlockRepo.get_by_page(pid)[0]
    cbw = ContentBlockWidget(block=block)
    cbw.show()
    yield cbw
    cbw.close()


def _get_task_blocks(body):
    return [el for el in body._blocks if el["type"] == "tasks"]


class TestEmbeddedContainerControls:
    def test_move_up_disabled_at_top(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        c = task_blocks[0]["widget"]
        assert c._up_btn.isEnabled() is False

    def test_move_down_disabled_at_bottom(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        c = task_blocks[0]["widget"]
        assert c._down_btn.isEnabled() is False

    def test_move_up_enabled_when_not_first(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        c = task_blocks[1]["widget"]
        assert c._up_btn.isEnabled() is True

    def test_move_down_enabled_when_not_last(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        c = task_blocks[0]["widget"]
        assert c._down_btn.isEnabled() is True

    def test_resize_handle_exists(self, text_block):
        from src.ui.editor import MarkdownBlock, _EmbeddedResizeHandle

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        c = task_blocks[0]["widget"]
        assert isinstance(c._resize_handle, _EmbeddedResizeHandle)

    def test_resize_minimum_height(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        c = task_blocks[0]["widget"]
        assert c._min_height == 60

    def test_button_states_after_add_three(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        body.add_task_list()
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        assert task_blocks[0]["widget"]._up_btn.isEnabled() is False
        assert task_blocks[0]["widget"]._down_btn.isEnabled() is True
        assert task_blocks[1]["widget"]._up_btn.isEnabled() is True
        assert task_blocks[1]["widget"]._down_btn.isEnabled() is True
        assert task_blocks[2]["widget"]._up_btn.isEnabled() is True
        assert task_blocks[2]["widget"]._down_btn.isEnabled() is False

    def test_button_states_after_remove_middle(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        body.add_task_list()
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        middle = task_blocks[1]["widget"]
        body._remove_embedded_list(middle)
        task_blocks = _get_task_blocks(body)
        assert len(task_blocks) == 2
        assert task_blocks[0]["widget"]._up_btn.isEnabled() is False
        assert task_blocks[0]["widget"]._down_btn.isEnabled() is True
        assert task_blocks[1]["widget"]._up_btn.isEnabled() is True
        assert task_blocks[1]["widget"]._down_btn.isEnabled() is False


class TestStandaloneList:
    def test_creates_with_initial_task(self, app_instance, db_init):
        from src.models.content_block import ContentBlock
        from src.models.page import Page
        from src.repositories.block_repo import BlockRepo
        from src.repositories.page_repo import PageRepo
        from src.ui.editor import PageEditor, TaskWidget

        pid = PageRepo.create(Page(title="Test"))
        BlockRepo.create(
            ContentBlock(page_id=pid, block_type="text", content_markdown="Hi")
        )
        e = PageEditor()
        e.load_page(pid)
        e._add_block("list")
        list_w = e._block_widgets[-1]
        body = list_w._body
        assert isinstance(body, TaskWidget)
        layout = body.layout()
        assert layout.count() >= 1
        e.close()

    def test_block_type_is_list(self, app_instance, db_init):
        from src.models.content_block import ContentBlock
        from src.models.page import Page
        from src.repositories.block_repo import BlockRepo
        from src.repositories.page_repo import PageRepo
        from src.ui.editor import PageEditor

        pid = PageRepo.create(Page(title="Test"))
        BlockRepo.create(
            ContentBlock(page_id=pid, block_type="text", content_markdown="Hi")
        )
        e = PageEditor()
        e.load_page(pid)
        e._add_block("list")
        assert e._block_widgets[-1].block.block_type == "list"
        e.close()

    def test_standalone_independent_of_table(self, app_instance, db_init):
        from src.models.content_block import ContentBlock
        from src.models.page import Page
        from src.repositories.block_repo import BlockRepo
        from src.repositories.page_repo import PageRepo
        from src.ui.editor import PageEditor

        pid = PageRepo.create(Page(title="Test"))
        BlockRepo.create(
            ContentBlock(page_id=pid, block_type="text", content_markdown="Hi")
        )
        e = PageEditor()
        e.load_page(pid)
        e._add_block("list")
        list_block = e._block_widgets[-1]
        assert list_block.block.block_type == "list"
        assert list_block.block.page_id == pid
        e.close()


class TestCanvasDeselect:
    def test_canvas_click_clears_selection(self, app_instance, db_init):
        from src.models.content_block import ContentBlock
        from src.models.page import Page
        from src.repositories.block_repo import BlockRepo
        from src.repositories.page_repo import PageRepo
        from src.ui.editor import PageEditor

        pid = PageRepo.create(Page(title="Test"))
        BlockRepo.create(
            ContentBlock(page_id=pid, block_type="text", content_markdown="Hi")
        )
        e = PageEditor()
        e.load_page(pid)
        e._block_widgets[0].set_selected(True)
        e._block_widgets[0]._selected = True
        assert e._block_widgets[0]._selected is True
        e._on_canvas_clicked(500, 500)
        assert e._block_widgets[0]._selected is False
        e.close()
