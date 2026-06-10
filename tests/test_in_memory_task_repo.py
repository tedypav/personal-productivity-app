import pytest
from src.models.task import Task
from src.repositories.in_memory_task_repo import InMemoryTaskRepo


@pytest.fixture
def repo():
    return InMemoryTaskRepo()


class TestInMemoryTaskRepoCreate:
    def test_assigns_auto_incrementing_id(self, repo):
        t1 = Task(content_block_id=1, text="T1")
        t2 = Task(content_block_id=1, text="T2")
        repo.create(t1)
        repo.create(t2)
        assert t1.id == 0
        assert t2.id == 1

    def test_auto_computes_sort_order(self, repo):
        t1 = Task(content_block_id=1, text="T1")
        t2 = Task(content_block_id=1, text="T2")
        repo.create(t1)
        repo.create(t2)
        assert t1.sort_order == 0
        assert t2.sort_order == 1

    def test_create_on_empty_gives_sort_order_0(self, repo):
        t = Task(content_block_id=1, text="T")
        repo.create(t)
        assert t.sort_order == 0

    def test_returns_id(self, repo):
        t = Task(content_block_id=1, text="T")
        tid = repo.create(t)
        assert tid == 0


class TestInMemoryTaskRepoRead:
    def test_get_by_block_filters(self, repo):
        repo.create(Task(content_block_id=1, text="A"))
        repo.create(Task(content_block_id=2, text="B"))
        repo.create(Task(content_block_id=1, text="C"))
        result = repo.get_by_block(1)
        assert len(result) == 2
        assert all(t.content_block_id == 1 for t in result)

    def test_get_by_block_empty(self, repo):
        assert repo.get_by_block(99) == []

    def test_get_by_block_returns_new_list(self, repo):
        repo.create(Task(content_block_id=1, text="T"))
        r1 = repo.get_by_block(1)
        r2 = repo.get_by_block(1)
        assert r1 is not r2


class TestInMemoryTaskRepoUpdate:
    def test_updates_task(self, repo):
        t = Task(content_block_id=1, text="Old")
        repo.create(t)
        t.text = "New"
        t.is_checked = True
        t.recurrence_type = "daily"
        t.due_date = "2024-06-15"
        t.sort_order = 5
        repo.update(t)
        result = repo.get_by_block(1)
        assert result[0].text == "New"
        assert result[0].is_checked is True
        assert result[0].recurrence_type == "daily"
        assert result[0].due_date == "2024-06-15"
        assert result[0].sort_order == 5

    def test_update_does_not_copy_content_block_id(self, repo):
        t = Task(content_block_id=1, text="T")
        repo.create(t)
        update_task = Task(id=t.id, content_block_id=99, text="Updated")
        repo.update(update_task)
        result = repo.get_by_block(1)
        assert len(result) == 1
        assert result[0].content_block_id == 1

    def test_update_nonexistent_silent(self, repo):
        t = Task(id=999, content_block_id=1, text="X")
        repo.update(t)
        assert len(repo.get_by_block(1)) == 0


class TestInMemoryTaskRepoDelete:
    def test_deletes_task(self, repo):
        t = Task(content_block_id=1, text="T")
        tid = repo.create(t)
        repo.delete(tid)
        assert repo.get_by_block(1) == []

    def test_delete_nonexistent_noop(self, repo):
        repo.delete(999)
        assert repo.get_by_block(1) == []

    def test_delete_by_block(self, repo):
        repo.create(Task(content_block_id=1, text="A"))
        repo.create(Task(content_block_id=1, text="B"))
        repo.create(Task(content_block_id=2, text="C"))
        repo.delete_by_block(1)
        assert repo.get_by_block(1) == []
        assert len(repo.get_by_block(2)) == 1
