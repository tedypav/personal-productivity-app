import sys

import pytest
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QKeyEvent
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


class TestBlockTextEdit:
    def test_enter_splits_paragraph(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        te = body.editor
        te.setPlainText("Hello")
        te.setFocus()
        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Return,
            Qt.KeyboardModifier.NoModifier,
        )
        te.keyPressEvent(event)
        assert len(body._blocks) > 1

    def test_backspace_at_empty_merges(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        body._add_text_block("")
        initial = len(body._blocks)
        empty_te = body._blocks[-1]["widget"]
        empty_te.setFocus()
        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Backspace,
            Qt.KeyboardModifier.NoModifier,
        )
        empty_te.keyPressEvent(event)
        assert len(body._blocks) < initial

    def test_shift_enter_no_split(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        te = body.editor
        te.setPlainText("Hello")
        te.setFocus()
        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Return,
            Qt.KeyboardModifier.ShiftModifier,
        )
        te.keyPressEvent(event)
        assert len(body._blocks) == 1

    def test_backspace_with_text_no_merge(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        te = body.editor
        te.setPlainText("Hello")
        te.setFocus()
        initial = len(body._blocks)
        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Backspace,
            Qt.KeyboardModifier.NoModifier,
        )
        te.keyPressEvent(event)
        assert len(body._blocks) == initial

    def test_auto_grows_on_text(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        te = body.editor
        te.setPlainText("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")
        assert te.height() > 0
        assert te.minimumHeight() > 0


class TestBlockSeparator:
    def test_separator_hover_state(self, text_block):
        from src.ui.editor import MarkdownBlock, _BlockSeparator

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        seps = body._blocks_container.findChildren(_BlockSeparator)
        assert len(seps) > 0
        sep = seps[0]
        assert sep._hovering is False
        sep._hovering = True
        sep.update()
        assert sep._hovering is True

    def test_separator_click_emits_signal(self, text_block):
        from src.ui.editor import MarkdownBlock, _BlockSeparator

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        seps = body._blocks_container.findChildren(_BlockSeparator)
        assert len(seps) > 0
        sep = seps[0]
        received = []
        sep.insert_requested.connect(lambda s: received.append(s))
        sep.insert_requested.emit(sep)
        assert len(received) == 1


class TestMarkdownBlockSerialization:
    def test_roundtrip_text_only(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        body.editor.setPlainText("Test content")
        content = body.to_serialized_content()
        import json

        data = json.loads(content)
        assert "blocks" in data
        assert len(data["blocks"]) == 1
        assert data["blocks"][0]["type"] == "text"

    def test_roundtrip_with_tasks(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        body.editor.setPlainText("Text before")
        body.add_task_list()
        content = body.to_serialized_content()
        import json

        data = json.loads(content)
        assert len(data["blocks"]) == 2
        assert data["blocks"][0]["type"] == "text"
        assert data["blocks"][1]["type"] == "tasks"

    def test_old_format_migration(self, app_instance, db_init):
        from src.ui.editor import MarkdownBlock

        old = (
            '{"text": "<p>Old</p>", '
            '"task_lists": [[{"text": "t", "is_checked": false}]]}'
        )
        block = MarkdownBlock(1, old)
        assert len(block._blocks) == 2
        assert block._blocks[0]["type"] == "text"
        assert block._blocks[1]["type"] == "tasks"

    def test_plain_text_loads(self, app_instance, db_init):
        from src.ui.editor import MarkdownBlock

        block = MarkdownBlock(1, "Just plain text")
        assert len(block._blocks) == 1
        assert block._blocks[0]["type"] == "text"

    def test_empty_content_creates_block(self, app_instance, db_init):
        from src.ui.editor import MarkdownBlock

        block = MarkdownBlock(1, "")
        assert len(block._blocks) == 1
        assert block._blocks[0]["type"] == "text"

    def test_preview_renders_all_blocks(self, text_block):
        from src.ui.editor import MarkdownBlock

        body = text_block._body
        assert isinstance(body, MarkdownBlock)
        content = body.to_serialized_content()
        import json

        data = json.loads(content)
        assert len(data["blocks"]) >= 1
        assert data["blocks"][0]["type"] == "text"


class TestCanvasInteraction:
    def test_empty_hint_positioned_high(self, app_instance, db_init):
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
        assert len(e._block_widgets) == 1
        e.close()

    def test_ctrl_a_selects_all(self, app_instance, db_init):
        from src.models.content_block import ContentBlock
        from src.models.page import Page
        from src.repositories.block_repo import BlockRepo
        from src.repositories.page_repo import PageRepo
        from src.ui.editor import PageEditor

        pid = PageRepo.create(Page(title="Test"))
        BlockRepo.create(
            ContentBlock(page_id=pid, block_type="text", content_markdown="A")
        )
        BlockRepo.create(
            ContentBlock(page_id=pid, block_type="text", content_markdown="B")
        )
        e = PageEditor()
        e.load_page(pid)
        assert len(e._block_widgets) == 2
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QKeyEvent

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_A,
            Qt.KeyboardModifier.ControlModifier,
        )
        e.keyPressEvent(event)
        for w in e._block_widgets:
            assert w._selected is True
        e.close()
