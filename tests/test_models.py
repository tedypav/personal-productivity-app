import pytest
from src.models.page import Page
from src.models.content_block import ContentBlock
from src.models.task import Task
from src.models.template import Template


class TestPage:
    def test_construction_defaults(self):
        p = Page()
        assert p.id is None
        assert p.title == "Untitled"
        assert p.parent_id is None
        assert p.sort_order == 0
        assert p.page_type == "page"
        assert p.created_at is None
        assert p.updated_at is None

    def test_construction_explicit(self):
        p = Page(id=1, title="Test", parent_id=5, sort_order=3, page_type="folder",
                 created_at="2024-01-01", updated_at="2024-01-02")
        assert p.id == 1
        assert p.title == "Test"
        assert p.parent_id == 5
        assert p.sort_order == 3
        assert p.page_type == "folder"
        assert p.created_at == "2024-01-01"
        assert p.updated_at == "2024-01-02"

    def test_equality(self):
        p1 = Page(id=1, title="A")
        p2 = Page(id=1, title="A")
        assert p1 == p2

    def test_inequality(self):
        p1 = Page(id=1, title="A")
        p2 = Page(id=2, title="A")
        assert p1 != p2


class TestContentBlock:
    def test_construction_defaults(self):
        b = ContentBlock()
        assert b.id is None
        assert b.page_id is None
        assert b.block_type == "text"
        assert b.content_markdown == ""
        assert b.sort_order == 0
        assert b.height is None
        assert b.width is None
        assert b.header is None
        assert b.header_font_size is None
        assert b.header_align_h == "left"
        assert b.header_align_v == "center"
        assert b.header_height is None
        assert b.content_font_size is None
        assert b.pos_x == 0
        assert b.pos_y == 0

    def test_construction_explicit(self):
        b = ContentBlock(id=1, page_id=10, block_type="table",
                         content_markdown="| a |", sort_order=2,
                         height=300, width=400, header="My Block",
                         header_font_size=16, content_font_size=14,
                         header_align_h="center", header_align_v="top",
                         header_height=50, pos_x=100, pos_y=200)
        assert b.id == 1
        assert b.height == 300
        assert b.width == 400
        assert b.header == "My Block"

    def test_normalize_font_size_none(self):
        assert ContentBlock._normalize_font_size(None) is None

    def test_normalize_font_size_zero(self):
        assert ContentBlock._normalize_font_size(0) is None

    def test_normalize_font_size_negative(self):
        assert ContentBlock._normalize_font_size(-5) is None

    def test_normalize_font_size_string(self):
        assert ContentBlock._normalize_font_size("abc") is None

    def test_normalize_font_size_valid(self):
        assert ContentBlock._normalize_font_size(14) == 14

    def test_normalize_font_size_float(self):
        assert ContentBlock._normalize_font_size(14.7) == 14

    def test_normalize_font_size_bool(self):
        assert ContentBlock._normalize_font_size(True) == 1

    def test_post_init_normalizes_header_font_size(self):
        b = ContentBlock(header_font_size=0)
        assert b.header_font_size is None

    def test_post_init_normalizes_content_font_size(self):
        b = ContentBlock(content_font_size=-3)
        assert b.content_font_size is None

    def test_post_init_valid_font_sizes(self):
        b = ContentBlock(header_font_size=16, content_font_size=12)
        assert b.header_font_size == 16
        assert b.content_font_size == 12


class TestTask:
    def test_construction_defaults(self):
        t = Task()
        assert t.id is None
        assert t.content_block_id is None
        assert t.text == ""
        assert t.is_checked is False
        assert t.recurrence_type == "none"
        assert t.due_date is None
        assert t.parent_task_id is None
        assert t.sort_order == 0

    def test_construction_explicit(self):
        t = Task(id=1, content_block_id=5, text="Buy milk",
                 is_checked=True, recurrence_type="weekly",
                 due_date="2024-06-15", parent_task_id=3, sort_order=2)
        assert t.id == 1
        assert t.is_checked is True
        assert t.recurrence_type == "weekly"

    def test_is_checked_round_trip(self):
        t = Task(is_checked=True)
        assert t.is_checked is True
        assert int(t.is_checked) == 1

    def test_is_checked_false(self):
        t = Task(is_checked=False)
        assert int(t.is_checked) == 0


class TestTemplate:
    def test_construction_defaults(self):
        t = Template()
        assert t.id is None
        assert t.name == ""
        assert t.category == "General"
        assert t.content_json == "[]"
        assert t.created_at is None

    def test_construction_explicit(self):
        t = Template(id=1, name="My Template", category="Work",
                     content_json='[{"type":"text"}]', created_at="2024-01-01")
        assert t.id == 1
        assert t.name == "My Template"
        assert t.category == "Work"
        assert t.content_json == '[{"type":"text"}]'
