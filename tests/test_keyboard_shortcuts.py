import sys
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.database import init_db
from src.models.page import Page
from src.models.content_block import ContentBlock
from src.repositories.page_repo import PageRepo
from src.repositories.block_repo import BlockRepo
from src.undo_manager import undo_manager, _page_dict


@pytest.fixture
def db_init():
    init_db()


@pytest.fixture
def main_window(app_instance, db_init):
    from src.ui.main_window import MainWindow
    mw = MainWindow()
    yield mw
    mw.close()


class TestKeyboardShortcuts:
    def test_toggle_sidebar(self, main_window):
        visible = main_window.sidebar.isVisible()
        main_window._toggle_sidebar()
        assert main_window.sidebar.isVisible() != visible

    def test_undo_delete(self, main_window):
        pid = PageRepo.create(Page(title="UndoMe"))
        PageRepo.delete(pid)
        undo_manager.push({
            "type": "page",
            "page": {
                "id": pid, "title": "UndoMe", "parent_id": None,
                "sort_order": 0, "page_type": "page",
                "created_at": None, "updated_at": None,
            },
            "blocks": [], "tasks": [], "children": [],
        })
        main_window._undo_delete()
        restored = PageRepo.get_by_id(pid)
        assert restored is not None
