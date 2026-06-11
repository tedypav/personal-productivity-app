import os
import sqlite3
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def mock_qmessagebox():
    """Mock QMessageBox to prevent dialogs from blocking tests."""
    mock_instance = MagicMock()
    mock_instance.exec.return_value = 0
    mock_instance.clickedButton.return_value = MagicMock()

    with (
        patch("PyQt6.QtWidgets.QMessageBox", mock_instance),
        patch("src.ui.editor.QMessageBox", mock_instance),
        patch("src.ui.sidebar.QMessageBox", mock_instance),
        patch("src.ui.main_window.QMessageBox", mock_instance),
    ):
        yield


@pytest.fixture(scope="session")
def temp_db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except PermissionError:
        pass


@pytest.fixture(autouse=True)
def patch_db(temp_db_path, monkeypatch):
    monkeypatch.setattr("src.database.DB_PATH", temp_db_path)
    import src.database as db_mod

    db_mod.DB_PATH = temp_db_path

    original_connect = sqlite3.connect

    def connect_with_timeout(path, *args, **kwargs):
        kwargs.setdefault("timeout", 5)
        return original_connect(path, *args, **kwargs)

    monkeypatch.setattr("sqlite3.connect", connect_with_timeout)

    from src.database import init_db

    init_db()

    conn = sqlite3.connect(temp_db_path, timeout=5)
    conn.execute("PRAGMA foreign_keys=ON")
    for table in ("tasks", "content_blocks", "pages", "templates"):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()


@pytest.fixture(scope="session")
def app_instance():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def page_repo():
    from src.repositories.page_repo import PageRepo

    return PageRepo()


@pytest.fixture
def block_repo():
    from src.repositories.block_repo import BlockRepo

    return BlockRepo()


@pytest.fixture
def task_repo():
    from src.repositories.task_repo import TaskRepo

    return TaskRepo()


@pytest.fixture
def template_repo():
    from src.repositories.template_repo import TemplateRepo

    return TemplateRepo()


@pytest.fixture
def undo_mgr():
    from src.undo_manager import UndoManager

    return UndoManager()


@pytest.fixture
def in_memory_task_repo():
    from src.repositories.in_memory_task_repo import InMemoryTaskRepo

    return InMemoryTaskRepo()
