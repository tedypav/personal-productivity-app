import sys
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.database import init_db
from src.models.page import Page
from src.models.content_block import ContentBlock
from src.repositories.page_repo import PageRepo
from src.repositories.block_repo import BlockRepo
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


class TestTaskWidgetSetRecurrence:
    def test_set_recurrence(self, task_widget):
        task_widget._add_task()
        task = task_widget.task_repo._tasks[0]
        task_widget._set_recurrence(task, "weekly")
        assert task_widget.task_repo._tasks[0].recurrence_type == "weekly"


class TestTaskWidgetDeleteTask:
    def test_delete_task(self, task_widget):
        task_widget._add_task()
        task = task_widget.task_repo._tasks[0]
        task_widget._delete_task(task)
        assert len(task_widget.task_repo._tasks) == 0


class TestRecurringTaskCopy:
    def test_create_recurring_copy(self, task_widget):
        from src.models.task import Task
        task = Task(content_block_id=1, text="Weekly task",
                    recurrence_type="weekly", due_date="2024-06-10")
        task_widget._create_recurring_copy(task)
        assert len(task_widget.task_repo._tasks) == 1
        new_task = task_widget.task_repo._tasks[0]
        assert new_task.due_date == "2024-06-17"
