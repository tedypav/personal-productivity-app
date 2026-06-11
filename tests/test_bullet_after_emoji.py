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
    yield cbw
    cbw.close()


class TestBulletAfterEmoji:
    def test_bullet_after_single_emoji(self, text_block):
        """Insert one emoji then bullet - must not crash."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        cursor = edit.textCursor()
        cursor.insertText("😀")
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "bullet", text_block)
        assert "😀" in edit.toPlainText()

    def test_bullet_after_multiple_emojis(self, text_block):
        """Insert multiple emojis then bullet."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        cursor = edit.textCursor()
        cursor.insertText("😀🎉🚀")
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "bullet", text_block)
        assert "😀🎉🚀" in edit.toPlainText()

    def test_bullet_after_emoji_and_text(self, text_block):
        """Insert emoji, text, then bullet."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        cursor = edit.textCursor()
        cursor.insertText("Hello 😀 World")
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "bullet", text_block)
        assert "Hello" in edit.toPlainText()

    def test_bold_after_emoji(self, text_block):
        """Bold after emoji must not crash."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        cursor = edit.textCursor()
        cursor.insertText("😀 Bold")
        edit.setTextCursor(cursor)
        cursor = edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "bold", text_block)
        assert "Bold" in edit.toPlainText()

    def test_italic_after_emoji(self, text_block):
        """Italic after emoji must not crash."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        cursor = edit.textCursor()
        cursor.insertText("😀 Italic")
        edit.setTextCursor(cursor)
        cursor = edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "italic", text_block)
        assert "Italic" in edit.toPlainText()

    def test_h1_after_emoji(self, text_block):
        """H1 after emoji must not crash."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        cursor = edit.textCursor()
        cursor.insertText("😀 Heading")
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "h1", text_block)
        assert "Heading" in edit.toPlainText()

    def test_h2_after_emoji(self, text_block):
        """H2 after emoji must not crash."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        cursor = edit.textCursor()
        cursor.insertText("😀 Subheading")
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "h2", text_block)
        assert "Subheading" in edit.toPlainText()

    def test_code_after_emoji(self, text_block):
        """Code after emoji must not crash."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        cursor = edit.textCursor()
        cursor.insertText("😀 Code")
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "code", text_block)
        assert "Code" in edit.toPlainText()

    def test_repeated_format_cycle(self, text_block):
        """Repeatedly alternate formatting and emoji insertion."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        from src.ui.editor import _apply_format_to_edit

        for i in range(5):
            cursor = edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.insertText(f"😀{i}")
            edit.setTextCursor(cursor)

            cursor = edit.textCursor()
            cursor.select(cursor.SelectionType.Document)
            edit.setTextCursor(cursor)

            fmts = ["bold", "italic", "h1", "h2", "code", "bullet"]
            _apply_format_to_edit(edit, fmts[i % len(fmts)], text_block)

        text = edit.toPlainText()
        assert "😀0" in text
        assert "😀4" in text
