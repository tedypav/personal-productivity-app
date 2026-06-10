import sys
import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication

from src.database import init_db
from src.models.page import Page
from src.models.content_block import ContentBlock
from src.repositories.page_repo import PageRepo
from src.repositories.block_repo import BlockRepo


@pytest.fixture
def db_init():
    init_db()


@pytest.fixture
def main_window(app_instance, db_init):
    from src.ui.main_window import MainWindow
    mw = MainWindow()
    yield mw
    mw.close()


class TestMainWindowRendering:
    def test_creates_with_sidebar_and_editor(self, main_window):
        assert main_window.sidebar is not None
        assert main_window.editor is not None

    def test_has_menu_bar(self, main_window):
        menubar = main_window.menuBar()
        assert menubar is not None


class TestMainWindowMenus:
    def test_has_file_menu(self, main_window):
        menubar = main_window.menuBar()
        actions = [a.text() for a in menubar.actions()]
        assert any("File" in a for a in actions)


class TestMainWindowToggleSidebar:
    def test_toggle_sidebar(self, main_window):
        visible = main_window.sidebar.isVisible()
        main_window._toggle_sidebar()
        assert main_window.sidebar.isVisible() != visible
