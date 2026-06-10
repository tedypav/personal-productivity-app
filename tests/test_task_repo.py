import pytest
from src.database import init_db
from src.models.page import Page
from src.models.content_block import ContentBlock
from src.models.task import Task
from src.repositories.page_repo import PageRepo
from src.repositories.block_repo import BlockRepo
from src.repositories.task_repo import TaskRepo


@pytest.fixture
def db_init():
    init_db()


@pytest.fixture
def task_repo():
    return TaskRepo()


@pytest.fixture
def block_repo():
    return BlockRepo()


@pytest.fixture
def sample_block(block_repo, page_repo):
    pid = page_repo.create(Page(title="p"))
    return block_repo.create(ContentBlock(page_id=pid, block_type="text"))


@pytest.fixture
def page_repo():
    return PageRepo()


class TestTaskRepoCreate:
    def test_creates_task_and_returns_id(self, task_repo, sample_block):
        task_id = task_repo.create(Task(content_block_id=sample_block, text="Buy milk"))
        assert task_id > 0

    def test_auto_computes_sort_order(self, task_repo, sample_block):
        t1 = Task(content_block_id=sample_block, text="T1")
        t2 = Task(content_block_id=sample_block, text="T2")
        task_repo.create(t1)
        task_repo.create(t2)
        tasks = task_repo.get_by_block(sample_block)
        assert tasks[0].sort_order == 0
        assert tasks[1].sort_order == 1

    def test_stores_is_checked_as_int(self, task_repo, sample_block):
        tid = task_repo.create(Task(content_block_id=sample_block, text="T", is_checked=True))
        tasks = task_repo.get_by_block(sample_block)
        assert tasks[0].is_checked == 1

    def test_stores_recurrence_type(self, task_repo, sample_block):
        tid = task_repo.create(Task(content_block_id=sample_block, text="T", recurrence_type="weekly"))
        tasks = task_repo.get_by_block(sample_block)
        assert tasks[0].recurrence_type == "weekly"


class TestTaskRepoRead:
    def test_get_by_block_returns_tasks(self, task_repo, sample_block):
        task_repo.create(Task(content_block_id=sample_block, text="T1"))
        tasks = task_repo.get_by_block(sample_block)
        assert len(tasks) == 1

    def test_get_by_block_empty(self, task_repo, sample_block):
        tasks = task_repo.get_by_block(sample_block)
        assert tasks == []

    def test_get_by_block_ordered(self, task_repo, sample_block):
        task_repo.create(Task(content_block_id=sample_block, text="B"))
        task_repo.create(Task(content_block_id=sample_block, text="A"))
        tasks = task_repo.get_by_block(sample_block)
        assert tasks[0].sort_order <= tasks[1].sort_order


class TestTaskRepoUpdate:
    def test_updates_task(self, task_repo, sample_block):
        tid = task_repo.create(Task(content_block_id=sample_block, text="Old"))
        task = task_repo.get_by_block(sample_block)[0]
        task.text = "New"
        task.is_checked = True
        task.recurrence_type = "daily"
        task.due_date = "2024-06-15"
        task_repo.update(task)
        updated = task_repo.get_by_block(sample_block)
        assert updated[0].text == "New"
        assert updated[0].is_checked == 1
        assert updated[0].recurrence_type == "daily"
        assert updated[0].due_date == "2024-06-15"

    def test_update_preserves_content_block_id(self, task_repo, sample_block):
        tid = task_repo.create(Task(content_block_id=sample_block, text="T"))
        task = task_repo.get_by_block(sample_block)[0]
        original_block_id = task.content_block_id
        task.text = "Changed"
        task_repo.update(task)
        updated = task_repo.get_by_block(sample_block)
        assert updated[0].content_block_id == original_block_id


class TestTaskRepoDelete:
    def test_deletes_task(self, task_repo, sample_block):
        tid = task_repo.create(Task(content_block_id=sample_block, text="T"))
        task_repo.delete(tid)
        assert task_repo.get_by_block(sample_block) == []

    def test_delete_by_block(self, task_repo, sample_block):
        task_repo.create(Task(content_block_id=sample_block, text="T1"))
        task_repo.create(Task(content_block_id=sample_block, text="T2"))
        task_repo.delete_by_block(sample_block)
        assert task_repo.get_by_block(sample_block) == []
