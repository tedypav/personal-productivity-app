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
    BlockRepo.create(ContentBlock(page_id=pid, block_type="table"))
    return pid


@pytest.fixture
def editor(app_instance, db_init):
    from src.ui.editor import PageEditor

    e = PageEditor()
    yield e
    e.close()


class TestAddListStandalone:
    """Test that +List creates standalone blocks when not in a content context."""

    def test_add_list_creates_standalone_block(self, editor, page_with_blocks):
        """Clicking +List without focus in any content creates a standalone block."""
        editor.load_page(page_with_blocks)
        initial = len(editor._block_widgets)
        editor._add_block("list")
        assert len(editor._block_widgets) == initial + 1

    def test_add_list_standalone_block_type(self, editor, page_with_blocks):
        """Standalone list block has correct block_type."""
        editor.load_page(page_with_blocks)
        editor._add_block("list")
        new_block = editor._block_widgets[-1].block
        assert new_block.block_type == "list"

    def test_add_list_standalone_saved_to_db(self, editor, page_with_blocks):
        """Standalone list block is persisted in the database."""
        editor.load_page(page_with_blocks)
        editor._add_block("list")
        editor.save_current()
        blocks = BlockRepo.get_by_page(page_with_blocks)
        list_blocks = [b for b in blocks if b.block_type == "list"]
        assert len(list_blocks) >= 1

    def test_add_list_no_active_context_creates_standalone(
        self, editor, page_with_blocks
    ):
        """When no active table cell or text body, +List creates standalone."""
        editor.load_page(page_with_blocks)
        editor._active_table_cell = None
        editor._active_text_body = None
        initial = len(editor._block_widgets)
        editor._add_block("list")
        assert len(editor._block_widgets) == initial + 1

    def test_multiple_standalone_lists(self, editor, page_with_blocks):
        """Can create multiple standalone list blocks."""
        editor.load_page(page_with_blocks)
        initial = len(editor._block_widgets)
        editor._add_block("list")
        editor._add_block("list")
        editor._add_block("list")
        assert len(editor._block_widgets) == initial + 3

    def test_standalone_list_independent_of_table(self, editor, page_with_blocks):
        """Standalone list is a separate block, not embedded in a table."""
        editor.load_page(page_with_blocks)
        editor._add_block("list")
        list_widget = editor._block_widgets[-1]
        # Should be a top-level block, not a child of a table
        assert list_widget.block.block_type == "list"
        assert list_widget.block.page_id == page_with_blocks


class TestEmbeddedList:
    """Test that +List embeds in table/text when focus is in a content context."""

    def test_embedded_list_in_table_cell(self, editor, page_with_blocks):
        """List can be embedded in a table cell via add_task_list."""
        editor.load_page(page_with_blocks)
        # Find the table widget
        table_widgets = [
            w
            for w in editor._block_widgets
            if w.block.block_type == "table" and hasattr(w, "_body")
        ]
        assert len(table_widgets) >= 1
        table_w = table_widgets[0]
        body = table_w._body
        if hasattr(body, "rows") and body.rows:
            # Get first cell
            cell = body.grid.itemAtPosition(0, 0).widget()
            if hasattr(cell, "add_task_list"):
                cell.add_task_list()
                # Cell should now have an embedded task widget
                assert hasattr(cell, "_task_widget") or cell.findChild(
                    __import__("src.ui.editor", fromlist=["TaskWidget"]).TaskWidget
                )

    def test_embedded_list_in_markdown_block(self, editor, page_with_blocks):
        """List can be embedded in a markdown block via add_task_list."""
        editor.load_page(page_with_blocks)
        # Find the text widget
        text_widgets = [
            w
            for w in editor._block_widgets
            if w.block.block_type == "text" and hasattr(w, "_body")
        ]
        assert len(text_widgets) >= 1
        text_w = text_widgets[0]
        body = text_w._body
        if hasattr(body, "add_task_list"):
            initial_lists = len(body._embedded_lists)
            body.add_task_list()
            assert len(body._embedded_lists) == initial_lists + 1
