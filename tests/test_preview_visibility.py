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


@pytest.fixture
def text_block(app_instance, db_init):
    from src.ui.editor import ContentBlockWidget

    pid = PageRepo.create(Page(title="Test"))
    BlockRepo.create(
        ContentBlock(
            page_id=pid,
            block_type="text",
            content_markdown="<p>Hello</p>",
        )
    )
    block = BlockRepo.get_by_page(pid)[0]
    cbw = ContentBlockWidget(block=block)
    cbw.show()
    yield cbw
    cbw.close()


class TestPreviewVisible:
    def test_plain_text_shows_in_preview(self, text_block):
        """Plain text should be visible in preview mode."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        edit.setPlainText("Hello World")
        body._switch_to_preview()
        preview_text = body.preview.toPlainText()
        assert "Hello World" in preview_text

    def test_emoji_shows_in_preview(self, text_block):
        """Emoji should be visible in preview mode."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        cursor = edit.textCursor()
        cursor.insertText("Hello 😀 World")
        edit.setTextCursor(cursor)
        body._switch_to_preview()
        preview_text = body.preview.toPlainText()
        assert "Hello" in preview_text
        assert "World" in preview_text

    def test_bullet_shows_in_preview(self, text_block):
        """Bulleted text should be visible in preview mode."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "bullet", text_block)
        cursor = edit.textCursor()
        cursor.insertText("List item")
        edit.setTextCursor(cursor)
        body._switch_to_preview()
        preview_text = body.preview.toPlainText()
        assert "List item" in preview_text

    def test_bold_shows_in_preview(self, text_block):
        """Bold text should be visible in preview mode."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        cursor = edit.textCursor()
        cursor.insertText("Bold text")
        edit.setTextCursor(cursor)
        cursor = edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        edit.setTextCursor(cursor)
        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "bold", text_block)
        body._switch_to_preview()
        preview_text = body.preview.toPlainText()
        assert "Bold text" in preview_text

    def test_heading_shows_in_preview(self, text_block):
        """Heading text should be visible in preview mode."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        cursor = edit.textCursor()
        cursor.insertText("My Heading")
        edit.setTextCursor(cursor)
        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "h1", text_block)
        body._switch_to_preview()
        preview_text = body.preview.toPlainText()
        assert "My Heading" in preview_text

    def test_content_persists_after_edit_preview_cycle(self, text_block):
        """Content should survive multiple edit->preview->edit cycles."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        edit.setPlainText("Cycle test")
        body._switch_to_preview()
        body._switch_to_edit()
        body._switch_to_preview()
        preview_text = body.preview.toPlainText()
        assert "Cycle test" in preview_text

    def test_multiline_text_in_preview(self, text_block):
        """Multi-line text should be visible in preview mode."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        edit.setPlainText("Line 1\nLine 2\nLine 3")
        body._switch_to_preview()
        preview_text = body.preview.toPlainText()
        assert "Line 1" in preview_text
        assert "Line 2" in preview_text
        assert "Line 3" in preview_text

    def test_html_content_shows_in_preview(self, text_block):
        """HTML content should be visible in preview mode."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        edit.setHtml("<p><b>Bold HTML</b></p>")
        body._switch_to_preview()
        preview_text = body.preview.toPlainText()
        assert "Bold HTML" in preview_text
