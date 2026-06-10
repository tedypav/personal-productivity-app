import pytest
from src.database import init_db
from src.models.template import Template
from src.repositories.template_repo import TemplateRepo


@pytest.fixture
def db_init():
    init_db()


@pytest.fixture
def repo():
    return TemplateRepo()


class TestTemplateRepoCreate:
    def test_creates_template_and_returns_id(self, repo, db_init):
        tid = repo.create(Template(name="My Template"))
        assert tid > 0

    def test_stores_all_fields(self, repo, db_init):
        repo.create(Template(name="T", category="Work", content_json='[{"a":1}]'))
        templates = repo.get_all()
        assert len(templates) == 1
        assert templates[0].name == "T"
        assert templates[0].category == "Work"
        assert templates[0].content_json == '[{"a":1}]'


class TestTemplateRepoRead:
    def test_get_by_id(self, repo, db_init):
        tid = repo.create(Template(name="Find"))
        found = repo.get_by_id(tid)
        assert found is not None
        assert found.name == "Find"

    def test_get_by_id_none_for_nonexistent(self, repo, db_init):
        assert repo.get_by_id(99999) is None

    def test_get_all_sorted(self, repo, db_init):
        repo.create(Template(name="B", category="Z"))
        repo.create(Template(name="A", category="A"))
        templates = repo.get_all()
        assert templates[0].category == "A"
        assert templates[1].category == "Z"

    def test_get_all_empty(self, repo, db_init):
        assert repo.get_all() == []


class TestTemplateRepoDelete:
    def test_deletes_template(self, repo, db_init):
        tid = repo.create(Template(name="Delete"))
        repo.delete(tid)
        assert repo.get_by_id(tid) is None

    def test_delete_all(self, repo, db_init):
        repo.create(Template(name="T1"))
        repo.create(Template(name="T2"))
        repo.delete_all()
        assert repo.get_all() == []


class TestTemplateRepoEdgeCases:
    def test_same_name_different_categories(self, repo, db_init):
        repo.create(Template(name="Report", category="Work"))
        repo.create(Template(name="Report", category="Personal"))
        templates = repo.get_all()
        assert len(templates) == 2
