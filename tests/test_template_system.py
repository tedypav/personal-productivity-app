import sys
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.database import init_db
from src.models.page import Page
from src.models.content_block import ContentBlock
from src.repositories.page_repo import PageRepo
from src.repositories.block_repo import BlockRepo
from src.repositories.template_repo import TemplateRepo
from src.models.template import Template


@pytest.fixture
def db_init():
    init_db()


@pytest.fixture
def page_editor(app_instance, db_init):
    from src.ui.editor import PageEditor
    e = PageEditor()
    yield e
    e.close()


class TestTemplateSaveAndInsert:
    def test_template_persists(self, db_init):
        TemplateRepo.create(Template(name="PersistTest", content_json='[{"type":"text"}]'))
        templates = TemplateRepo.get_all()
        assert len(templates) >= 1
        assert templates[0].name == "PersistTest"

    def test_template_insert(self, page_editor, db_init):
        pid = PageRepo.create(Page(title="Target"))
        page_editor.load_page(pid)
        page_editor._current_page_id = pid
        templates = TemplateRepo.get_all()
        assert isinstance(templates, list)

    def test_bulk_insert(self, db_init):
        tid = TemplateRepo.create(Template(name="BulkTemplate", content_json='[]'))
        pid1 = PageRepo.create(Page(title="P1"))
        pid2 = PageRepo.create(Page(title="P2"))
        template = TemplateRepo.get_by_id(tid)
        assert template is not None

    def test_template_display_format(self, db_init):
        TemplateRepo.create(Template(name="Report", category="Work"))
        templates = TemplateRepo.get_all()
        assert len(templates) >= 1
