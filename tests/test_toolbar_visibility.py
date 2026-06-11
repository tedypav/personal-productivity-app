import sys

import pytest
from PyQt6.QtCore import Qt
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


class TestToolbarVisibility:
    def test_toolbar_hidden_on_creation(self, text_block):
        """Inline toolbar starts hidden."""
        text_block._inline_toolbar.setVisible(False)
        assert text_block._inline_toolbar.isHidden() is True

    def test_toolbar_shows_on_text_edit(self, text_block):
        """Toolbar shows when text block enters edit mode."""
        body = text_block._body
        body._switch_to_edit()
        assert text_block._inline_toolbar.isHidden() is False

    def test_toolbar_hides_on_preview(self, text_block):
        """Toolbar hides when text block enters preview mode."""
        body = text_block._body
        body._switch_to_edit()
        assert text_block._inline_toolbar.isHidden() is False
        body._switch_to_preview()
        assert text_block._inline_toolbar.isHidden() is True

    def test_toolbar_shows_on_header_focus(self, text_block):
        """Toolbar shows when header is focused."""
        text_block.header_focused.emit(text_block)
        assert text_block._inline_toolbar.isHidden() is False

    def test_toolbar_hides_on_header_focus_out(self, text_block):
        """Toolbar hides when header loses focus and not editing."""
        text_block.header_focused.emit(text_block)
        assert text_block._inline_toolbar.isHidden() is False
        from PyQt6.QtGui import QFocusEvent

        text_block._header_edit.focusOutEvent(QFocusEvent(QFocusEvent.Type.FocusOut))
        assert text_block._inline_toolbar.isHidden() is True

    def test_toolbar_stays_on_header_focus_out_when_editing(self, text_block):
        """Toolbar stays visible when header loses focus but text body is editing."""
        body = text_block._body
        body._switch_to_edit()
        text_block.header_focused.emit(text_block)
        from PyQt6.QtGui import QFocusEvent

        text_block._header_edit.focusOutEvent(QFocusEvent(QFocusEvent.Type.FocusOut))
        assert text_block._inline_toolbar.isHidden() is False

    def test_toolbar_has_formatting_buttons(self, text_block):
        """Toolbar contains all expected formatting buttons."""
        tb = text_block._inline_toolbar
        from PyQt6.QtWidgets import QComboBox, QToolButton

        buttons = tb.findChildren(QToolButton)
        combos = tb.findChildren(QComboBox)
        assert len(buttons) >= 7
        assert len(combos) >= 1

    def test_toolbar_bold_button_works(self, text_block):
        """Clicking bold button applies formatting."""
        body = text_block._body
        body._switch_to_edit()
        edit = body.editor
        cursor = edit.textCursor()
        cursor.insertText("Test text")
        edit.setTextCursor(cursor)
        cursor = edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        edit.setTextCursor(cursor)
        text_block._in_bold_btn.click()
        fmt = edit.textCursor().charFormat()
        from PyQt6.QtGui import QFont

        assert fmt.fontWeight() >= QFont.Weight.Bold


class TestHeaderColor:
    def test_header_text_not_gray(self, text_block):
        """Header text color should be dark, not gray."""
        header = text_block._header_edit
        header.setPlainText("Test Header")
        color = header.textColor().name()
        assert color != "#9ca3af"

    def test_header_text_is_dark(self, text_block):
        """Header text should be a dark color."""
        header = text_block._header_edit
        header.setPlainText("Test Header")
        color = header.textColor().name()
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        assert r < 100 and g < 100 and b < 100


class TestHeaderButtonsInPreview:
    def test_dots_btn_hidden_in_preview(self, text_block):
        """Dots/alignment menu button hides in preview mode."""
        body = text_block._body
        body._switch_to_edit()
        body._switch_to_preview()
        assert text_block._dots_btn.isHidden() is True

    def test_dots_btn_shows_in_edit(self, text_block):
        """Dots/alignment menu button shows in edit mode."""
        body = text_block._body
        body._switch_to_preview()
        body._switch_to_edit()
        assert text_block._dots_btn.isHidden() is False

    def test_fun_imports_btn_hidden_in_preview(self, text_block):
        """Emoji/Fun Imports button hides in preview mode."""
        body = text_block._body
        body._switch_to_edit()
        body._switch_to_preview()
        assert text_block._fun_imports_btn.isHidden() is True

    def test_fun_imports_btn_shows_in_edit(self, text_block):
        """Emoji/Fun Imports button shows in edit mode."""
        body = text_block._body
        body._switch_to_preview()
        body._switch_to_edit()
        assert text_block._fun_imports_btn.isHidden() is False

    def test_header_centered_in_preview(self, text_block):
        """Header is centered when in preview mode."""
        body = text_block._body
        body._switch_to_edit()
        body._switch_to_preview()
        align = text_block._header_edit.alignment()
        assert align == Qt.AlignmentFlag.AlignCenter

    def test_header_alignment_respects_user_setting(self, text_block):
        """Header keeps user-set alignment when switching back to edit."""
        body = text_block._body
        text_block._header_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        body._switch_to_edit()
        body._switch_to_preview()
        body._switch_to_edit()
        align = text_block._header_edit.alignment()
        assert align == Qt.AlignmentFlag.AlignLeft

    def test_all_header_buttons_restore_on_edit(self, text_block):
        """All header buttons restore after edit-preview-edit cycle."""
        body = text_block._body
        body._switch_to_edit()
        body._switch_to_preview()
        body._switch_to_edit()
        assert text_block._dots_btn.isHidden() is False
        assert text_block._fun_imports_btn.isHidden() is False
        assert text_block._inline_toolbar.isHidden() is False

    def test_dots_btn_shows_on_header_focus(self, text_block):
        """Alignment dots button shows when header is focused."""
        text_block.header_focused.emit(text_block)
        assert text_block._dots_btn.isHidden() is False

    def test_fun_imports_btn_shows_on_header_focus(self, text_block):
        """Emoji button shows when header is focused."""
        text_block.header_focused.emit(text_block)
        assert text_block._fun_imports_btn.isHidden() is False

    def test_all_buttons_hide_on_canvas_click(self, text_block):
        """All formatting buttons hide when focus goes to None (canvas click)."""
        body = text_block._body
        body._switch_to_edit()
        body._switch_to_preview()
        assert text_block._inline_toolbar.isHidden() is True
        assert text_block._dots_btn.isHidden() is True
        assert text_block._fun_imports_btn.isHidden() is True
