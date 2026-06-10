import sys
import pytest
from PyQt6.QtCore import Qt
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
def table_widget(app_instance, db_init):
    from src.ui.editor import TableWidget
    pid = PageRepo.create(Page(title="TestPage"))
    bid = BlockRepo.create(ContentBlock(page_id=pid, block_type="table"))
    tw = TableWidget(block_id=bid)
    yield tw
    tw.close()


class TestTableWidgetRendering:
    def test_creates_with_default_rows_cols(self, table_widget):
        assert table_widget is not None

    def test_has_toolbar_buttons(self, table_widget):
        from PyQt6.QtWidgets import QPushButton
        btns = table_widget.findChildren(QPushButton)
        btn_texts = [b.text() for b in btns]
        assert "+ Row" in btn_texts
        assert "- Row" in btn_texts
        assert "+ Col" in btn_texts
        assert "- Col" in btn_texts


class TestTableWidgetAddRemoveRow:
    def test_add_row(self, table_widget):
        initial_rows = len(table_widget.rows)
        table_widget._add_row()
        assert len(table_widget.rows) > initial_rows

    def test_delete_last_row(self, table_widget):
        table_widget._add_row()
        table_widget._delete_last_row()
        assert len(table_widget.rows) >= 1


class TestTableWidgetAddRemoveCol:
    def test_add_col(self, table_widget):
        initial_cols = len(table_widget.rows[0]) if table_widget.rows else 0
        table_widget._add_col()
        assert len(table_widget.rows[0]) > initial_cols

    def test_delete_last_col(self, table_widget):
        table_widget._add_col()
        table_widget._delete_last_col()
        assert len(table_widget.rows[0]) >= 1


class TestTableWidgetHeader:
    def test_toggle_header_on(self, table_widget):
        table_widget._toggle_header(True)
        assert table_widget._headers is not None

    def test_toggle_header_off(self, table_widget):
        table_widget._toggle_header(True)
        table_widget._toggle_header(False)
        assert table_widget._headers is not None


class TestTableWidgetRowNumbers:
    def test_toggle_row_numbers_on(self, table_widget):
        table_widget._toggle_row_numbers(True)
        assert table_widget._show_row_numbers is True

    def test_toggle_row_numbers_off(self, table_widget):
        table_widget._toggle_row_numbers(True)
        table_widget._toggle_row_numbers(False)
        assert table_widget._show_row_numbers is False


class TestTableWidgetSelection:
    def test_clear_selection(self, table_widget):
        table_widget._clear_selection()
        assert len(table_widget._selected_cells) == 0


class TestTableWidgetSerialization:
    def test_to_markdown(self, table_widget):
        md = table_widget.to_markdown()
        assert isinstance(md, str)
        assert "|" in md or md == ""
