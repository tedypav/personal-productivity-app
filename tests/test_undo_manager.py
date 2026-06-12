from datetime import datetime, timedelta

import pytest

from src.models.page import Page
from src.repositories.page_repo import PageRepo
from src.undo_manager import (
    UNDO_DURATION,
    UndoManager,
    _capture_children,
    _page_dict,
    capture_page_tree,
)


@pytest.fixture
def undo_mgr():
    return UndoManager()


class TestUndoManager:
    def test_starts_empty(self, undo_mgr):
        assert len(undo_mgr._actions) == 0

    def test_push_adds_action(self, undo_mgr):
        action = {"type": "page", "page": _page_dict(Page(title="t")), "children": []}
        undo_mgr.push(action)
        assert len(undo_mgr._actions) == 1
        assert "timestamp" in undo_mgr._actions[0]

    def test_pop_returns_most_recent(self, undo_mgr):
        pid1 = PageRepo().create(Page(title="first"))
        pid2 = PageRepo().create(Page(title="second"))
        p1 = _page_dict(Page(id=pid1, title="first"))
        p2 = _page_dict(Page(id=pid2, title="second"))
        undo_mgr.push({"type": "page", "page": p1, "children": []})
        undo_mgr.push({"type": "page", "page": p2, "children": []})
        PageRepo().delete(pid1)
        PageRepo().delete(pid2)
        result = undo_mgr.pop()
        assert result["page"]["title"] == "second"

    def test_pop_on_empty_returns_none(self, undo_mgr):
        assert undo_mgr.pop() is None

    def test_can_undo_true(self, undo_mgr):
        undo_mgr.push({"type": "page", "data": "test"})
        assert undo_mgr.can_undo() is True

    def test_can_undo_false_when_empty(self, undo_mgr):
        assert undo_mgr.can_undo() is False

    def test_prune_removes_expired(self, undo_mgr):
        action = {"type": "page", "page": _page_dict(Page(title="old")), "children": []}
        undo_mgr.push(action)
        undo_mgr._actions[0]["timestamp"] = (
            datetime.now() - UNDO_DURATION - timedelta(seconds=1)
        )
        new_action = {
            "type": "page",
            "page": _page_dict(Page(title="new")),
            "children": [],
        }
        undo_mgr.push(new_action)
        assert len(undo_mgr._actions) == 1

    def test_prune_keeps_recent(self, undo_mgr):
        action = {"type": "page", "page": _page_dict(Page(title="t")), "children": []}
        undo_mgr.push(action)
        assert len(undo_mgr._actions) == 1

    def test_pop_restores_page(self, undo_mgr):
        pid = PageRepo().create(Page(title="UndoTest"))
        PageRepo().delete(pid)
        assert PageRepo().get_by_id(pid) is None
        undo_mgr.push(
            {
                "type": "page",
                "page": _page_dict(Page(id=pid, title="UndoTest")),
                "children": [],
            }
        )
        undo_mgr.pop()
        restored = PageRepo().get_by_id(pid)
        assert restored is not None
        assert restored.title == "UndoTest"

    def test_pop_restores_bulk_pages(self, undo_mgr):
        pid1 = PageRepo().create(Page(title="bulk1"))
        pid2 = PageRepo().create(Page(title="bulk2"))
        undo_mgr.push(
            {
                "type": "bulk",
                "actions": [
                    {
                        "type": "page",
                        "page": _page_dict(Page(id=pid1, title="bulk1")),
                        "children": [],
                    },
                    {
                        "type": "page",
                        "page": _page_dict(Page(id=pid2, title="bulk2")),
                        "children": [],
                    },
                ],
            }
        )
        PageRepo().delete(pid1)
        PageRepo().delete(pid2)
        undo_mgr.pop()
        assert PageRepo().get_by_id(pid1) is not None
        assert PageRepo().get_by_id(pid2) is not None

    def test_multiple_undos_lifo(self, undo_mgr):
        pid1 = PageRepo().create(Page(title="first"))
        pid2 = PageRepo().create(Page(title="second"))
        undo_mgr.push(
            {
                "type": "page",
                "page": _page_dict(Page(id=pid1, title="first")),
                "children": [],
            }
        )
        undo_mgr.push(
            {
                "type": "page",
                "page": _page_dict(Page(id=pid2, title="second")),
                "children": [],
            }
        )
        PageRepo().delete(pid1)
        PageRepo().delete(pid2)
        undo_mgr.pop()
        assert PageRepo().get_by_id(pid2) is not None
        undo_mgr.pop()
        assert PageRepo().get_by_id(pid1) is not None


class TestCapturePageTree:
    def test_captures_page(self):
        pid = PageRepo().create(Page(title="CaptureTest"))
        result = capture_page_tree(pid)
        assert result is not None
        assert result["page"]["title"] == "CaptureTest"

    def test_captures_children(self):
        parent = PageRepo().create(Page(title="parent"))
        PageRepo().create(Page(title="child", parent_id=parent))
        result = capture_page_tree(parent)
        assert len(result["children"]) == 1
        assert result["children"][0]["page"]["title"] == "child"

    def test_returns_none_for_nonexistent(self):
        assert capture_page_tree(99999) is None


class TestCaptureChildren:
    def test_returns_empty_for_no_children(self):
        pid = PageRepo().create(Page(title="no children"))
        result = _capture_children(pid)
        assert result == []

    def test_captures_nested_children(self):
        p1 = PageRepo().create(Page(title="p1"))
        p2 = PageRepo().create(Page(title="p2", parent_id=p1))
        PageRepo().create(Page(title="p3", parent_id=p2))
        result = _capture_children(p1)
        assert len(result) == 1
        assert result[0]["page"]["title"] == "p2"
        assert len(result[0]["children"]) == 1
        assert result[0]["children"][0]["page"]["title"] == "p3"


class TestDictHelpers:
    def test_page_dict(self):
        p = Page(
            id=1,
            title="T",
            parent_id=2,
            sort_order=3,
            page_type="folder",
            created_at="2024-01-01",
            updated_at="2024-01-02",
        )
        d = _page_dict(p)
        assert d["id"] == 1
        assert d["title"] == "T"
        assert d["parent_id"] == 2
