import pytest

from src.models.page import Page
from src.repositories.page_repo import PageRepo


@pytest.fixture
def repo():
    return PageRepo()


class TestPageRepoCreate:
    def test_creates_page_and_returns_id(self, repo):
        page_id = repo.create(Page(title="Test Page"))
        assert page_id is not None
        assert page_id > 0

    def test_auto_computes_sort_order_when_zero(self, repo):
        p1_id = repo.create(Page(title="P1"))
        p2_id = repo.create(Page(title="P2"))
        p1 = repo.get_by_id(p1_id)
        p2 = repo.get_by_id(p2_id)
        assert p1.sort_order == 0
        assert p2.sort_order == 1

    def test_uses_provided_sort_order(self, repo):
        p_id = repo.create(Page(title="P", sort_order=5))
        p = repo.get_by_id(p_id)
        assert p.sort_order == 5

    def test_sets_page_type(self, repo):
        p_id = repo.create(Page(title="Folder", page_type="folder"))
        p = repo.get_by_id(p_id)
        assert p.page_type == "folder"

    def test_auto_assigns_title_default(self, repo):
        p_id = repo.create(Page())
        p = repo.get_by_id(p_id)
        assert p.title == "Untitled"


class TestPageRepoRead:
    def test_get_by_id_returns_page(self, repo):
        p_id = repo.create(Page(title="Find Me"))
        found = repo.get_by_id(p_id)
        assert found is not None
        assert found.title == "Find Me"

    def test_get_by_id_returns_none_for_nonexistent(self, repo):
        assert repo.get_by_id(99999) is None

    def test_get_all_returns_all_pages(self, repo):
        repo.create(Page(title="A"))
        repo.create(Page(title="B"))
        all_pages = repo.get_all()
        assert len(all_pages) == 2

    def test_get_all_sorted_by_sort_order(self, repo):
        repo.create(Page(title="B", sort_order=2))
        repo.create(Page(title="A", sort_order=1))
        all_pages = repo.get_all()
        assert all_pages[0].title == "A"
        assert all_pages[1].title == "B"

    def test_get_children_root(self, repo):
        root_id = repo.create(Page(title="Root"))
        repo.create(Page(title="Child", parent_id=root_id))
        roots = repo.get_children(None)
        assert len(roots) == 1
        assert roots[0].title == "Root"

    def test_get_children_specific_parent(self, repo):
        parent_id = repo.create(Page(title="Parent"))
        repo.create(Page(title="Child1", parent_id=parent_id))
        repo.create(Page(title="Child2", parent_id=parent_id))
        children = repo.get_children(parent_id)
        assert len(children) == 2


class TestPageRepoUpdate:
    def test_updates_page(self, repo):
        p_id = repo.create(Page(title="Old Title"))
        page = repo.get_by_id(p_id)
        page.title = "New Title"
        repo.update(page)
        updated = repo.get_by_id(p_id)
        assert updated.title == "New Title"

    def test_updates_parent_id(self, repo):
        p1_id = repo.create(Page(title="P1"))
        p2_id = repo.create(Page(title="P2"))
        page = repo.get_by_id(p2_id)
        page.parent_id = p1_id
        repo.update(page)
        children = repo.get_children(p1_id)
        assert len(children) == 1

    def test_update_refreshes_updated_at(self, repo):
        p_id = repo.create(Page(title="P"))
        page = repo.get_by_id(p_id)
        repo.update(page)
        updated = repo.get_by_id(p_id)
        assert updated.updated_at is not None


class TestPageRepoDelete:
    def test_deletes_page(self, repo):
        p_id = repo.create(Page(title="Delete Me"))
        repo.delete(p_id)
        assert repo.get_by_id(p_id) is None

    def test_delete_cascades_to_children(self, repo):
        parent_id = repo.create(Page(title="Parent"))
        child_id = repo.create(Page(title="Child", parent_id=parent_id))
        repo.delete(parent_id)
        assert repo.get_by_id(child_id) is None


class TestPageRepoReorder:
    def test_reorder_updates_sort_order(self, repo):
        p_id = repo.create(Page(title="P", sort_order=1))
        repo.reorder(p_id, 5, None)
        page = repo.get_by_id(p_id)
        assert page.sort_order == 5

    def test_reorder_updates_parent(self, repo):
        p1_id = repo.create(Page(title="P1"))
        p2_id = repo.create(Page(title="P2"))
        repo.reorder(p2_id, 0, p1_id)
        page = repo.get_by_id(p2_id)
        assert page.parent_id == p1_id
