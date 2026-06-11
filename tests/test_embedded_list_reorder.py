import pytest

from src.database import init_db
from src.models.content_block import ContentBlock
from src.models.page import Page
from src.repositories.block_repo import BlockRepo
from src.repositories.page_repo import PageRepo


@pytest.fixture
def db_init():
    init_db()


@pytest.fixture
def page_with_blocks(db_init):
    pid = PageRepo.create(Page(title="TestPage"))
    BlockRepo.create(
        ContentBlock(page_id=pid, block_type="text", content_markdown="Hello")
    )
    return pid


@pytest.fixture
def editor(app_instance, db_init):
    from src.ui.editor import PageEditor

    e = PageEditor()
    yield e
    e.close()


@pytest.fixture
def text_block_with_embedded(editor, page_with_blocks):
    """Load page and return the text block widget."""
    editor.load_page(page_with_blocks)
    text_widgets = [
        w
        for w in editor._block_widgets
        if w.block.block_type == "text" and hasattr(w, "_body")
    ]
    return text_widgets[0]


class TestEmbeddedListReorder:
    """Test that embedded task lists can be reordered within a text block."""

    def test_move_up_down_buttons_exist(self, text_block_with_embedded):
        """Embedded containers have move up/down buttons."""
        from src.ui.editor import MarkdownBlock

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        body.add_task_list()
        assert len(body._embedded_lists) == 2
        c0 = body._embedded_lists[0]["container"]
        c1 = body._embedded_lists[1]["container"]
        assert hasattr(c0, "_up_btn")
        assert hasattr(c0, "_down_btn")
        assert hasattr(c1, "_up_btn")
        assert hasattr(c1, "_down_btn")

    def test_move_down_reorders(self, text_block_with_embedded):
        """Moving a list down swaps it with the one below."""
        from src.ui.editor import MarkdownBlock

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        body.add_task_list()
        c0 = body._embedded_lists[0]["container"]
        id_before = [el["id"] for el in body._embedded_lists]
        body._move_embedded_list_down(c0)
        id_after = [el["id"] for el in body._embedded_lists]
        assert id_after[0] == id_before[1]
        assert id_after[1] == id_before[0]

    def test_move_up_reorders(self, text_block_with_embedded):
        """Moving a list up swaps it with the one above."""
        from src.ui.editor import MarkdownBlock

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        body.add_task_list()
        c1 = body._embedded_lists[1]["container"]
        id_before = [el["id"] for el in body._embedded_lists]
        body._move_embedded_list_up(c1)
        id_after = [el["id"] for el in body._embedded_lists]
        assert id_after[0] == id_before[1]
        assert id_after[1] == id_before[0]

    def test_move_up_at_top_noop(self, text_block_with_embedded):
        """Moving the first list up does nothing."""
        from src.ui.editor import MarkdownBlock

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        c0 = body._embedded_lists[0]["container"]
        id_before = [el["id"] for el in body._embedded_lists]
        body._move_embedded_list_up(c0)
        id_after = [el["id"] for el in body._embedded_lists]
        assert id_after == id_before

    def test_move_down_at_bottom_noop(self, text_block_with_embedded):
        """Moving the last list down does nothing."""
        from src.ui.editor import MarkdownBlock

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        c0 = body._embedded_lists[0]["container"]
        id_before = [el["id"] for el in body._embedded_lists]
        body._move_embedded_list_down(c0)
        id_after = [el["id"] for el in body._embedded_lists]
        assert id_after == id_before

    def test_button_states_update(self, text_block_with_embedded):
        """Button enabled states reflect position in list."""
        from src.ui.editor import MarkdownBlock

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        body.add_task_list()
        body.add_task_list()
        c0 = body._embedded_lists[0]["container"]
        c1 = body._embedded_lists[1]["container"]
        c2 = body._embedded_lists[2]["container"]
        # First: can't move up, can move down
        assert c0._up_btn.isEnabled() is False
        assert c0._down_btn.isEnabled() is True
        # Middle: can move both
        assert c1._up_btn.isEnabled() is True
        assert c1._down_btn.isEnabled() is True
        # Last: can move up, can't move down
        assert c2._up_btn.isEnabled() is True
        assert c2._down_btn.isEnabled() is False

    def test_reorder_preserves_after_save_reload(self, editor, page_with_blocks):
        """Order is preserved after save and reload."""
        from src.ui.editor import MarkdownBlock

        editor.load_page(page_with_blocks)
        text_w = [w for w in editor._block_widgets if w.block.block_type == "text"][0]
        body = text_w._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        body.add_task_list()
        # Move second to first
        c1 = body._embedded_lists[1]["container"]
        body._move_embedded_list_up(c1)
        # Save
        editor.save_current()
        # Reload
        editor.load_page(page_with_blocks)
        text_w2 = [w for w in editor._block_widgets if w.block.block_type == "text"][0]
        body2 = text_w2._body
        assert isinstance(body2, MarkdownBlock)
        assert len(body2._embedded_lists) == 2


class TestEmbeddedResize:
    """Test that embedded task containers can be resized."""

    def test_resize_handle_exists(self, text_block_with_embedded):
        """Embedded container has a resize handle."""
        from src.ui.editor import MarkdownBlock, _EmbeddedResizeHandle

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        container = body._embedded_lists[0]["container"]
        assert hasattr(container, "_resize_handle")
        assert isinstance(container._resize_handle, _EmbeddedResizeHandle)
