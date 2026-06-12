from src.models.page import Page


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
        p = Page(
            id=1,
            title="Test",
            parent_id=5,
            sort_order=3,
            page_type="folder",
            created_at="2024-01-01",
            updated_at="2024-01-02",
        )
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
