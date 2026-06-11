import pytest
from PyQt6.QtCore import Qt

from src.database import init_db
from src.repositories.in_memory_task_repo import InMemoryTaskRepo


@pytest.fixture
def db_init():
    init_db()


@pytest.fixture
def task_widget(app_instance, db_init):
    from src.ui.editor import TaskWidget

    repo = InMemoryTaskRepo()
    tw = TaskWidget(block_id=1, task_repo=repo)
    yield tw
    tw.close()


class TestTaskWidgetRendering:
    def test_creates_empty(self, task_widget):
        assert task_widget is not None


class TestTaskWidgetAddTask:
    def test_add_task(self, task_widget):
        task_widget._add_task()
        assert len(task_widget.task_repo._tasks) == 1


class TestTaskWidgetToggleTask:
    def test_toggle_task(self, task_widget):
        task_widget._add_task()
        task = task_widget.task_repo._tasks[0]
        task_widget._toggle_task(task, Qt.CheckState.Checked.value)
        assert task_widget.task_repo._tasks[0].is_checked is True


class TestTaskWidgetUpdateText:
    def test_update_text(self, task_widget):
        task_widget._add_task()
        task = task_widget.task_repo._tasks[0]
        task_widget._update_text(task, "Updated text")
        assert task_widget.task_repo._tasks[0].text == "Updated text"


class TestTaskWidgetDeleteTask:
    def test_delete_task(self, task_widget):
        task_widget._add_task()
        task = task_widget.task_repo._tasks[0]
        task_widget._delete_task(task)
        assert len(task_widget.task_repo._tasks) == 0
