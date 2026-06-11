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


def _get_task_blocks(body):
    """Get task block entries from MarkdownBlock._blocks."""
    return [el for el in body._blocks if el["type"] == "tasks"]


class TestEmbeddedListReorder:
    """Test that embedded task lists can be reordered within a text block."""

    def test_move_up_down_buttons_exist(self, text_block_with_embedded):
        """Embedded containers have move up/down buttons."""
        from src.ui.editor import MarkdownBlock

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        assert len(task_blocks) == 2
        c0 = task_blocks[0]["widget"]
        c1 = task_blocks[1]["widget"]
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
        task_blocks = _get_task_blocks(body)
        c0 = task_blocks[0]["widget"]
        id_before = [el["id"] for el in task_blocks]
        body._move_embedded_list_down(c0)
        task_blocks = _get_task_blocks(body)
        id_after = [el["id"] for el in task_blocks]
        assert id_after[0] == id_before[1]
        assert id_after[1] == id_before[0]

    def test_move_up_reorders(self, text_block_with_embedded):
        """Moving a list up swaps it with the one above."""
        from src.ui.editor import MarkdownBlock

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        c1 = task_blocks[1]["widget"]
        id_before = [el["id"] for el in task_blocks]
        body._move_embedded_list_up(c1)
        task_blocks = _get_task_blocks(body)
        id_after = [el["id"] for el in task_blocks]
        assert id_after[0] == id_before[1]
        assert id_after[1] == id_before[0]

    def test_move_up_at_top_noop(self, text_block_with_embedded):
        """Moving the first list up does nothing."""
        from src.ui.editor import MarkdownBlock

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        c0 = task_blocks[0]["widget"]
        id_before = [el["id"] for el in task_blocks]
        body._move_embedded_list_up(c0)
        task_blocks = _get_task_blocks(body)
        id_after = [el["id"] for el in task_blocks]
        assert id_after == id_before

    def test_move_down_at_bottom_noop(self, text_block_with_embedded):
        """Moving the last list down does nothing."""
        from src.ui.editor import MarkdownBlock

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        c0 = task_blocks[0]["widget"]
        id_before = [el["id"] for el in task_blocks]
        body._move_embedded_list_down(c0)
        task_blocks = _get_task_blocks(body)
        id_after = [el["id"] for el in task_blocks]
        assert id_after == id_before

    def test_button_states_update(self, text_block_with_embedded):
        """Button enabled states reflect position in list."""
        from src.ui.editor import MarkdownBlock

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        body.add_task_list()
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        c0 = task_blocks[0]["widget"]
        c1 = task_blocks[1]["widget"]
        c2 = task_blocks[2]["widget"]
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
        task_blocks = _get_task_blocks(body)
        c1 = task_blocks[1]["widget"]
        body._move_embedded_list_up(c1)
        # Save
        editor.save_current()
        # Reload
        editor.load_page(page_with_blocks)
        text_w2 = [w for w in editor._block_widgets if w.block.block_type == "text"][0]
        body2 = text_w2._body
        assert isinstance(body2, MarkdownBlock)
        assert len(_get_task_blocks(body2)) == 2


class TestEmbeddedResize:
    """Test that embedded task containers can be resized."""

    def test_resize_handle_exists(self, text_block_with_embedded):
        """Embedded container has a resize handle."""
        from src.ui.editor import MarkdownBlock, _EmbeddedResizeHandle

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        container = task_blocks[0]["widget"]
        assert hasattr(container, "_resize_handle")
        assert isinstance(container._resize_handle, _EmbeddedResizeHandle)


class TestReorderPersistence:
    def test_reorder_preserves_task_data(self, text_block_with_embedded):
        from src.ui.editor import MarkdownBlock

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        repo0 = task_blocks[0]["repo"]
        repo1 = task_blocks[1]["repo"]
        tasks0_before = [t.text for t in repo0.get_by_block(task_blocks[0]["id"])]
        tasks1_before = [t.text for t in repo1.get_by_block(task_blocks[1]["id"])]
        c1 = task_blocks[1]["widget"]
        body._move_embedded_list_up(c1)
        task_blocks = _get_task_blocks(body)
        tasks0_after = [
            t.text for t in task_blocks[0]["repo"].get_by_block(task_blocks[0]["id"])
        ]
        tasks1_after = [
            t.text for t in task_blocks[1]["repo"].get_by_block(task_blocks[1]["id"])
        ]
        assert tasks0_after == tasks1_before
        assert tasks1_after == tasks0_before

    def test_resize_handle_has_minimum(self, text_block_with_embedded):
        from src.ui.editor import MarkdownBlock

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        c = task_blocks[0]["widget"]
        assert c._min_height == 60
        assert c._resize_handle is not None

    def test_multiple_task_lists_independent(self, text_block_with_embedded):
        from src.ui.editor import MarkdownBlock

        body = text_block_with_embedded._body
        assert isinstance(body, MarkdownBlock)
        body.add_task_list()
        body.add_task_list()
        task_blocks = _get_task_blocks(body)
        assert len(task_blocks) == 2
        repo0 = task_blocks[0]["repo"]
        repo1 = task_blocks[1]["repo"]
        tasks0 = repo0.get_by_block(task_blocks[0]["id"])
        tasks1 = repo1.get_by_block(task_blocks[1]["id"])
        assert len(tasks0) == 1
        assert len(tasks1) == 1
        assert tasks0[0].text == "New task"
        assert tasks1[0].text == "New task"
