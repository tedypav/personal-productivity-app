from datetime import datetime, timedelta

import pytest

from src.models.content_block import ContentBlock
from src.models.page import Page
from src.models.task import Task
from src.repositories.block_repo import BlockRepo
from src.repositories.page_repo import PageRepo
from src.repositories.task_repo import TaskRepo
from src.undo_manager import (
    UNDO_DURATION,
    UndoManager,
    _block_dict,
    _capture_children,
    _page_dict,
    _task_dict,
    capture_page_tree,
)


@pytest.fixture
def db_init():
    from src.database import init_db

    init_db()


@pytest.fixture
def undo_mgr():
    return UndoManager()


class TestUndoManager:
    def test_starts_empty(self, undo_mgr):
        assert len(undo_mgr._actions) == 0

    def test_push_adds_action(self, undo_mgr):
        undo_mgr.push({"type": "page", "data": "test"})
        assert len(undo_mgr._actions) == 1
        assert "timestamp" in undo_mgr._actions[0]

    def test_pop_returns_most_recent(self, undo_mgr, db_init):
        pid = PageRepo.create(Page(title="p"))
        bid = BlockRepo.create(ContentBlock(page_id=pid, block_type="text"))
        undo_mgr.push(
            {
                "type": "block",
                "block": {
                    "id": bid,
                    "page_id": pid,
                    "block_type": "text",
                    "content_markdown": "",
                    "sort_order": 0,
                },
                "tasks": [],
            }
        )
        undo_mgr.push(
            {
                "type": "task",
                "task": {
                    "id": 99,
                    "content_block_id": bid,
                    "text": "t",
                },
            }
        )
        result = undo_mgr.pop()
        assert result["type"] == "task"

    def test_pop_on_empty_returns_none(self, undo_mgr):
        assert undo_mgr.pop() is None

    def test_can_undo_true(self, undo_mgr):
        undo_mgr.push({"type": "task", "task": {}})
        assert undo_mgr.can_undo() is True

    def test_can_undo_false_when_empty(self, undo_mgr):
        assert undo_mgr.can_undo() is False

    def test_prune_removes_expired(self, undo_mgr):
        action = {"type": "page", "data": "old"}
        undo_mgr.push(action)
        undo_mgr._actions[0]["timestamp"] = (
            datetime.now() - UNDO_DURATION - timedelta(seconds=1)
        )
        undo_mgr.push({"type": "page", "data": "new"})
        assert len(undo_mgr._actions) == 1

    def test_prune_keeps_recent(self, undo_mgr):
        undo_mgr.push({"type": "task", "task": {}})
        assert len(undo_mgr._actions) == 1

    def test_pop_restores_page(self, undo_mgr, db_init):
        pid = PageRepo.create(Page(title="UndoTest"))
        bid = BlockRepo.create(ContentBlock(page_id=pid, block_type="text"))
        tid = TaskRepo.create(Task(content_block_id=bid, text="task1"))
        PageRepo.delete(pid)
        assert PageRepo.get_by_id(pid) is None
        undo_mgr.push(
            {
                "type": "page",
                "page": _page_dict(Page(id=pid, title="UndoTest")),
                "blocks": [
                    _block_dict(
                        ContentBlock(
                            id=bid,
                            page_id=pid,
                            block_type="text",
                        )
                    )
                ],
                "tasks": [_task_dict(Task(id=tid, content_block_id=bid, text="task1"))],
                "children": [],
            }
        )
        undo_mgr.pop()
        restored = PageRepo.get_by_id(pid)
        assert restored is not None
        assert restored.title == "UndoTest"

    def test_pop_restores_block(self, undo_mgr, db_init):
        pid = PageRepo.create(Page(title="p"))
        bid = BlockRepo.create(ContentBlock(page_id=pid, block_type="text"))
        BlockRepo.delete(bid)
        undo_mgr.push(
            {
                "type": "block",
                "block": _block_dict(
                    ContentBlock(id=bid, page_id=pid, block_type="text")
                ),
                "tasks": [],
            }
        )
        undo_mgr.pop()
        blocks = BlockRepo.get_by_page(pid)
        assert any(b.id == bid for b in blocks)

    def test_pop_restores_task(self, undo_mgr, db_init):
        pid = PageRepo.create(Page(title="p"))
        bid = BlockRepo.create(ContentBlock(page_id=pid, block_type="text"))
        tid = TaskRepo.create(Task(content_block_id=bid, text="my task"))
        TaskRepo.delete(tid)
        undo_mgr.push(
            {
                "type": "task",
                "task": _task_dict(Task(id=tid, content_block_id=bid, text="my task")),
            }
        )
        undo_mgr.pop()
        tasks = TaskRepo.get_by_block(bid)
        assert any(t.id == tid for t in tasks)

    def test_pop_restores_bulk_pages(self, undo_mgr, db_init):
        pid1 = PageRepo.create(Page(title="bulk1"))
        pid2 = PageRepo.create(Page(title="bulk2"))
        undo_mgr.push(
            {
                "type": "bulk",
                "actions": [
                    {
                        "type": "page",
                        "page": _page_dict(Page(id=pid1, title="bulk1")),
                        "blocks": [],
                        "tasks": [],
                        "children": [],
                    },
                    {
                        "type": "page",
                        "page": _page_dict(Page(id=pid2, title="bulk2")),
                        "blocks": [],
                        "tasks": [],
                        "children": [],
                    },
                ],
            }
        )
        PageRepo.delete(pid1)
        PageRepo.delete(pid2)
        undo_mgr.pop()
        assert PageRepo.get_by_id(pid1) is not None
        assert PageRepo.get_by_id(pid2) is not None

    def test_multiple_undos_lifo(self, undo_mgr, db_init):
        pid1 = PageRepo.create(Page(title="first"))
        pid2 = PageRepo.create(Page(title="second"))
        undo_mgr.push(
            {
                "type": "page",
                "page": _page_dict(Page(id=pid1, title="first")),
                "blocks": [],
                "tasks": [],
                "children": [],
            }
        )
        undo_mgr.push(
            {
                "type": "page",
                "page": _page_dict(Page(id=pid2, title="second")),
                "blocks": [],
                "tasks": [],
                "children": [],
            }
        )
        PageRepo.delete(pid1)
        PageRepo.delete(pid2)
        undo_mgr.pop()
        assert PageRepo.get_by_id(pid2) is not None
        undo_mgr.pop()
        assert PageRepo.get_by_id(pid1) is not None


class TestCapturePageTree:
    def test_captures_page(self, db_init):
        pid = PageRepo.create(Page(title="CaptureTest"))
        result = capture_page_tree(pid)
        assert result is not None
        assert result["page"]["title"] == "CaptureTest"

    def test_captures_blocks(self, db_init):
        pid = PageRepo.create(Page(title="p"))
        BlockRepo.create(ContentBlock(page_id=pid, block_type="text"))
        result = capture_page_tree(pid)
        assert len(result["blocks"]) == 1

    def test_captures_tasks(self, db_init):
        pid = PageRepo.create(Page(title="p"))
        bid = BlockRepo.create(ContentBlock(page_id=pid, block_type="text"))
        TaskRepo.create(Task(content_block_id=bid, text="t1"))
        result = capture_page_tree(pid)
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["text"] == "t1"

    def test_captures_children(self, db_init):
        parent = PageRepo.create(Page(title="parent"))
        PageRepo.create(Page(title="child", parent_id=parent))
        result = capture_page_tree(parent)
        assert len(result["children"]) == 1
        assert result["children"][0]["page"]["title"] == "child"

    def test_returns_none_for_nonexistent(self):
        assert capture_page_tree(99999) is None


class TestCaptureChildren:
    def test_returns_empty_for_no_children(self, db_init):
        pid = PageRepo.create(Page(title="no children"))
        result = _capture_children(pid)
        assert result == []

    def test_captures_nested_children(self, db_init):
        p1 = PageRepo.create(Page(title="p1"))
        p2 = PageRepo.create(Page(title="p2", parent_id=p1))
        PageRepo.create(Page(title="p3", parent_id=p2))
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

    def test_block_dict(self):
        b = ContentBlock(
            id=1, page_id=2, block_type="table", content_markdown="|a|", sort_order=5
        )
        d = _block_dict(b)
        assert d["id"] == 1
        assert d["page_id"] == 2
        assert d["block_type"] == "table"

    def test_task_dict(self):
        t = Task(
            id=1,
            content_block_id=2,
            text="hello",
            is_checked=True,
            recurrence_type="daily",
            due_date="2024-06-15",
            parent_task_id=3,
            sort_order=4,
        )
        d = _task_dict(t)
        assert d["id"] == 1
        assert d["is_checked"] is True
        assert d["recurrence_type"] == "daily"
