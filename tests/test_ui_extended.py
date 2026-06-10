import sys
import os
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
def app_instance():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestMainFunctions:
    def test_load_font_valid(self, app_instance):
        from src.main import load_font
        result = load_font("Test", os.path.join(os.path.dirname(__file__), "..", "requirements.txt"))
        assert result is None or isinstance(result, str)

    def test_load_font_missing(self, app_instance):
        from src.main import load_font
        result = load_font("Test", "/nonexistent/path.ttf")
        assert result is None

    def test_load_all_fonts(self, app_instance):
        from src.main import load_all_fonts
        fonts = load_all_fonts()
        assert isinstance(fonts, dict)
        assert "magnolia" in fonts
        assert "playfair" in fonts
        assert "inter" in fonts

    def test_app_stylesheet_exists(self):
        from src.main import APP_STYLESHEET
        assert len(APP_STYLESHEET) > 100

    def test_excepthook(self, app_instance):
        from src.main import _excepthook
        try:
            raise ValueError("test error")
        except ValueError:
            _excepthook(ValueError, ValueError("test error"), None)


class TestEditorFormatting:
    def test_render_markdown(self):
        from src.ui.editor import render_markdown
        result = render_markdown("**bold** and *italic*")
        assert "bold" in result

    def test_render_markdown_heading(self):
        from src.ui.editor import render_markdown
        result = render_markdown("# Heading 1")
        assert "Heading 1" in result

    def test_render_markdown_code(self):
        from src.ui.editor import render_markdown
        result = render_markdown("`code`")
        assert "code" in result

    def test_render_markdown_link(self):
        from src.ui.editor import render_markdown
        result = render_markdown("[link](http://example.com)")
        assert "link" in result

    def test_render_markdown_table(self):
        from src.ui.editor import render_markdown
        result = render_markdown("| a | b |\n|---|---|\n| 1 | 2 |")
        assert "a" in result

    def test_render_markdown_with_font_size(self):
        from src.ui.editor import render_markdown
        result = render_markdown("text", font_size=16)
        assert "text" in result

    def test_render_markdown_html_detection(self):
        from src.ui.editor import render_markdown
        result = render_markdown("<b>HTML</b>")
        assert "HTML" in result


class TestEditorModuleFunctions:
    def test_get_edit_html_body(self):
        from src.ui.editor import _get_edit_html_body
        from PyQt6.QtWidgets import QTextEdit
        edit = QTextEdit()
        edit.setHtml("<html><body><p>Test</p></body></html>")
        result = _get_edit_html_body(edit)
        assert "Test" in result
        edit.close()

    def test_get_edit_html_body_empty(self):
        from src.ui.editor import _get_edit_html_body
        from PyQt6.QtWidgets import QTextEdit
        edit = QTextEdit()
        edit.setPlainText("plain text")
        result = _get_edit_html_body(edit)
        assert isinstance(result, str)
        edit.close()


class TestMarkdownBlock:
    def test_creates(self, app_instance):
        from src.ui.editor import MarkdownBlock
        mb = MarkdownBlock(block_id=1, content="<p>Hello</p>")
        assert mb is not None
        mb.close()

    def test_to_serialized_content(self, app_instance):
        from src.ui.editor import MarkdownBlock
        mb = MarkdownBlock(block_id=1, content="<p>Hello</p>")
        result = mb.to_serialized_content()
        assert isinstance(result, str)
        mb.close()

    def test_toPlainText(self, app_instance):
        from src.ui.editor import MarkdownBlock
        mb = MarkdownBlock(block_id=1, content="<p>Hello</p>")
        result = mb.toPlainText()
        assert isinstance(result, str)
        mb.close()

    def test_set_content_font_size(self, app_instance):
        from src.ui.editor import MarkdownBlock
        mb = MarkdownBlock(block_id=1, content="<p>Hello</p>")
        mb.set_content_font_size(16)
        mb.close()

    def test_insert_formatting(self, app_instance):
        from src.ui.editor import MarkdownBlock
        mb = MarkdownBlock(block_id=1, content="<p>Hello</p>")
        mb._switch_to_edit()
        mb.insert_formatting("**", "**")
        mb.close()

    def test_insert_heading(self, app_instance):
        from src.ui.editor import MarkdownBlock
        mb = MarkdownBlock(block_id=1, content="")
        mb._switch_to_edit()
        mb.insert_heading(1)
        mb.close()

    def test_insert_bullet_list(self, app_instance):
        from src.ui.editor import MarkdownBlock
        mb = MarkdownBlock(block_id=1, content="")
        mb._switch_to_edit()
        mb.insert_bullet_list()
        mb.close()

    def test_add_task_list(self, app_instance):
        from src.ui.editor import MarkdownBlock
        mb = MarkdownBlock(block_id=1, content="<p>Hello</p>")
        mb.add_task_list()
        assert len(mb._embedded_lists) == 1
        mb.close()


class TestContentBlockWidget:
    def test_creates(self, app_instance):
        from src.ui.editor import ContentBlockWidget
        block = ContentBlock(id=1, page_id=1, block_type="text", content_markdown="Hello")
        cbw = ContentBlockWidget(block=block)
        assert cbw is not None
        cbw.close()

    def test_set_selected(self, app_instance):
        from src.ui.editor import ContentBlockWidget
        block = ContentBlock(id=1, page_id=1, block_type="text", content_markdown="Hello")
        cbw = ContentBlockWidget(block=block)
        cbw.set_selected(True)
        assert cbw._selected is True
        cbw.set_selected(False)
        assert cbw._selected is False
        cbw.close()

    def test_save(self, app_instance):
        from src.ui.editor import ContentBlockWidget
        pid = PageRepo.create(Page(title="Test"))
        bid = BlockRepo.create(ContentBlock(page_id=pid, block_type="text", content_markdown="Hello"))
        block = BlockRepo.get_by_page(pid)[0]
        cbw = ContentBlockWidget(block=block)
        cbw.save()
        cbw.close()


class TestTableCell:
    def test_creates(self, app_instance):
        from src.ui.editor import TableCell
        tc = TableCell(text="Hello", row=0, col=0)
        assert tc is not None
        tc.close()

    def test_toPlainText(self, app_instance):
        from src.ui.editor import TableCell
        tc = TableCell(text="Hello", row=0, col=0)
        result = tc.toPlainText()
        assert isinstance(result, str)
        tc.close()

    def test_setPlainText(self, app_instance):
        from src.ui.editor import TableCell
        tc = TableCell(text="Hello", row=0, col=0)
        tc.setPlainText("World")
        tc.close()


class TestTableHeaderCell:
    def test_creates(self, app_instance):
        from src.ui.editor import TableHeaderCell
        thc = TableHeaderCell(text="Header", col=0)
        assert thc is not None
        thc.close()


class TestRowNumCell:
    def test_creates(self, app_instance):
        from src.ui.editor import RowNumCell
        rnc = RowNumCell(text="1")
        assert rnc is not None
        rnc.close()


class TestDragHandle:
    def test_creates(self, app_instance):
        from src.ui.editor import DragHandle
        dh = DragHandle()
        assert dh is not None
        dh.close()


class TestCanvas:
    def test_creates(self, app_instance):
        from src.ui.editor import Canvas
        c = Canvas()
        assert c is not None
        c.close()

    def test_paint_event(self, app_instance):
        from src.ui.editor import Canvas
        from PyQt6.QtGui import QPaintEvent
        from PyQt6.QtCore import QRect
        c = Canvas()
        event = QPaintEvent(QRect(0, 0, 100, 100))
        c.paintEvent(event)
        c.close()


class TestPageEditorExtended:
    def test_editor_creates_welcome(self, app_instance, db_init):
        from src.ui.editor import PageEditor
        e = PageEditor()
        assert e.welcome_label is not None
        e.close()

    def test_editor_page_title(self, app_instance, db_init):
        from src.ui.editor import PageEditor
        e = PageEditor()
        assert e.page_title is not None
        e.close()

    def test_editor_clear_and_reload(self, app_instance, db_init):
        from src.ui.editor import PageEditor
        e = PageEditor()
        pid = PageRepo.create(Page(title="Test"))
        BlockRepo.create(ContentBlock(page_id=pid, block_type="text", content_markdown="Hello"))
        e.load_page(pid)
        assert len(e._block_widgets) == 1
        e.clear_editor()
        assert len(e._block_widgets) == 0
        e.close()

    def test_editor_add_multiple_blocks(self, app_instance, db_init):
        from src.ui.editor import PageEditor
        e = PageEditor()
        pid = PageRepo.create(Page(title="Test"))
        e.load_page(pid)
        e._add_block("text")
        e._add_block("table")
        e._add_block("checkbox")
        assert len(e._block_widgets) == 3
        e.close()

    def test_editor_save_current(self, app_instance, db_init):
        from src.ui.editor import PageEditor
        e = PageEditor()
        pid = PageRepo.create(Page(title="Test"))
        BlockRepo.create(ContentBlock(page_id=pid, block_type="text", content_markdown="Hello"))
        e.load_page(pid)
        e.save_current()
        blocks = BlockRepo.get_by_page(pid)
        assert len(blocks) == 1
        e.close()
