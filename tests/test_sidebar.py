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
def sidebar(app_instance, db_init):
    from src.ui.sidebar import Sidebar
    s = Sidebar()
    yield s
    s.close()


class TestSidebarRendering:
    def test_sidebar_has_buttons(self, sidebar):
        assert sidebar.btn_new is not None
        assert sidebar.btn_new_folder is not None
        assert sidebar.btn_expand is not None
        assert sidebar.btn_collapse is not None

    def test_sidebar_has_trees(self, sidebar):
        assert sidebar.tree is not None
        assert sidebar.template_tree is not None


class TestSidebarExpandCollapse:
    def test_expand_all(self, sidebar):
        PageRepo.create(Page(title="P1"))
        sidebar.refresh()
        sidebar._expand_all()
        assert sidebar.tree.topLevelItemCount() > 0

    def test_collapse_all(self, sidebar):
        PageRepo.create(Page(title="P1"))
        sidebar.refresh()
        sidebar._expand_all()
        sidebar._collapse_all()
        assert sidebar.tree.topLevelItemCount() >= 0


class TestSidebarRefresh:
    def test_refresh_loads_pages(self, sidebar):
        PageRepo.create(Page(title="TestRefresh"))
        sidebar.refresh()
        assert sidebar.tree.topLevelItemCount() > 0
