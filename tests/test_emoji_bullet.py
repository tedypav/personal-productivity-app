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


class TestEmojiInsertion:
    def test_insert_emoji_empty_block(self, text_block):
        """Insert emoji into empty text block."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        edit.clear()
        cursor = edit.textCursor()
        cursor.insertText("😀")
        edit.setTextCursor(cursor)
        assert "😀" in edit.toPlainText()

    def test_insert_emoji_after_text(self, text_block):
        """Insert emoji after existing text."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        cursor = edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText("😀")
        edit.setTextCursor(cursor)
        assert "😀" in edit.toPlainText()

    def test_insert_multiple_emojis(self, text_block):
        """Insert multiple emojis with text between."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        cursor = edit.textCursor()
        cursor.insertText("😀")
        edit.setTextCursor(cursor)

        cursor = edit.textCursor()
        cursor.insertText(" some text ")
        edit.setTextCursor(cursor)

        cursor = edit.textCursor()
        cursor.insertText("🎉")
        edit.setTextCursor(cursor)

        text = edit.toPlainText()
        assert "😀" in text
        assert "🎉" in text
        assert "some text" in text

    def test_insert_emoji_then_bullet(self, text_block):
        """Insert emoji then bullet list."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        cursor = edit.textCursor()
        cursor.insertText("😀")
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "bullet", text_block)

        text = edit.toPlainText()
        assert "😀" in text

    def test_insert_bullet_after_emoji_and_text(self, text_block):
        """Insert bullet after emoji and text content."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        cursor = edit.textCursor()
        cursor.insertText("Hello 😀 World")
        edit.setTextCursor(cursor)

        cursor = edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "bullet", text_block)

        assert "Hello" in edit.toPlainText()

    def test_emoji_persists_after_preview_switch(self, text_block):
        """Emoji survives edit->preview->edit cycle."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        cursor = edit.textCursor()
        cursor.insertText("Test 😀 emoji")
        edit.setTextCursor(cursor)

        body._switch_to_preview()
        assert body.editing is False

        body._switch_to_edit()
        assert body.editing is True
        assert "😀" in edit.toPlainText()


class TestEmojiInHeader:
    def test_header_accepts_text(self, text_block):
        """Header edit accepts plain text."""
        header = text_block._header_edit
        header.setPlainText("My Header")
        assert header.toPlainText() == "My Header"

    def test_header_accepts_emoji(self, text_block):
        """Header edit accepts emoji via insertText."""
        header = text_block._header_edit
        cursor = header.textCursor()
        cursor.insertText("Header 😀")
        header.setTextCursor(cursor)
        assert "😀" in header.toPlainText()

    def test_header_emoji_persists(self, text_block):
        """Emoji in header survives save."""
        header = text_block._header_edit
        cursor = header.textCursor()
        cursor.insertText("📝 Notes")
        header.setTextCursor(cursor)
        text_block.save()
        assert "📝" in header.toPlainText()


class TestBulletInsertion:
    def test_bullet_empty_block(self, text_block):
        """Add bullet to empty block."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        edit.clear()

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "bullet", text_block)

        cursor = edit.textCursor()
        block = cursor.block()
        assert block.textList() is not None

    def test_bullet_with_text(self, text_block):
        """Add bullet to block with text."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        cursor = edit.textCursor()
        cursor.insertText("Hello World")
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "bullet", text_block)

        cursor = edit.textCursor()
        block = cursor.block()
        assert block.textList() is not None

    def test_bullet_after_emoji(self, text_block):
        """Add bullet after emoji."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        cursor = edit.textCursor()
        cursor.insertText("😀")
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "bullet", text_block)

        assert "😀" in edit.toPlainText()

    def test_multiple_bullets(self, text_block):
        """Add multiple bullets."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "bullet", text_block)
        cursor = edit.textCursor()
        cursor.insertText("Item 1")
        edit.setTextCursor(cursor)

        cursor = edit.textCursor()
        cursor.insertText("\n")
        edit.setTextCursor(cursor)

        _apply_format_to_edit(edit, "bullet", text_block)
        cursor = edit.textCursor()
        cursor.insertText("Item 2")
        edit.setTextCursor(cursor)

        assert "Item 1" in edit.toPlainText()
        assert "Item 2" in edit.toPlainText()


class TestFormatAfterRichContent:
    def test_bold_after_emoji(self, text_block):
        """Apply bold after inserting emoji."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        cursor = edit.textCursor()
        cursor.insertText("😀 Bold text")
        edit.setTextCursor(cursor)

        cursor = edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "bold", text_block)

        assert "Bold text" in edit.toPlainText()

    def test_italic_after_emoji(self, text_block):
        """Apply italic after inserting emoji."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        cursor = edit.textCursor()
        cursor.insertText("😀 Italic text")
        edit.setTextCursor(cursor)

        cursor = edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "italic", text_block)

        assert "Italic text" in edit.toPlainText()

    def test_heading_after_emoji(self, text_block):
        """Apply heading after inserting emoji."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        cursor = edit.textCursor()
        cursor.insertText("😀 Heading")
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "h1", text_block)

        assert "Heading" in edit.toPlainText()

    def test_code_after_emoji(self, text_block):
        """Apply code formatting after inserting emoji."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        cursor = edit.textCursor()
        cursor.insertText("😀 Code")
        edit.setTextCursor(cursor)

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "code", text_block)

        assert "Code" in edit.toPlainText()


class TestRichContentThenEmoji:
    def test_emoji_after_bold(self, text_block):
        """Insert emoji after bold text."""
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

        cursor = edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(" 😀")
        edit.setTextCursor(cursor)

        text = edit.toPlainText()
        assert "Bold text" in text
        assert "😀" in text

    def test_emoji_after_heading(self, text_block):
        """Insert emoji after heading."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "h1", text_block)
        cursor = edit.textCursor()
        cursor.insertText("Heading")
        edit.setTextCursor(cursor)

        cursor = edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(" 😀")
        edit.setTextCursor(cursor)

        text = edit.toPlainText()
        assert "Heading" in text
        assert "😀" in text

    def test_bullet_then_emoji(self, text_block):
        """Insert emoji after bullet."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        from src.ui.editor import _apply_format_to_edit

        _apply_format_to_edit(edit, "bullet", text_block)
        cursor = edit.textCursor()
        cursor.insertText("List item")
        edit.setTextCursor(cursor)

        cursor = edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(" 😀")
        edit.setTextCursor(cursor)

        text = edit.toPlainText()
        assert "List item" in text
        assert "😀" in text

    def test_repeated_format_and_emoji(self, text_block):
        """Repeatedly alternate between formatting and emoji."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor

        from src.ui.editor import _apply_format_to_edit

        for i in range(3):
            cursor = edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            if i % 2 == 0:
                cursor.insertText(f"😀{i}")
            else:
                _apply_format_to_edit(edit, "bullet", text_block)
                cursor = edit.textCursor()
                cursor.insertText(f"Item {i}")
            edit.setTextCursor(cursor)

        text = edit.toPlainText()
        assert "😀0" in text
        assert "Item 1" in text
        assert "😀2" in text
