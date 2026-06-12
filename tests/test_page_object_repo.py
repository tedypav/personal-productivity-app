import json

import pytest

from src.models.page import Page
from src.models.page_object import PageObject
from src.repositories.page_object_repo import PageObjectRepo
from src.repositories.page_repo import PageRepo


@pytest.fixture
def page_object_repo():
    return PageObjectRepo()


@pytest.fixture
def sample_page():
    return PageRepo().create(Page(title="TestPage"))


class TestPageObjectRepoCreate:
    def test_creates_object_and_returns_id(self, page_object_repo, sample_page):
        obj = PageObject(
            page_id=sample_page,
            object_type="checkbox",
            content=json.dumps({"text": "Test", "checked": False}),
        )
        obj_id = page_object_repo.create(obj)
        assert obj_id is not None

    def test_creates_multiple_objects(self, page_object_repo, sample_page):
        for i in range(3):
            obj = PageObject(
                page_id=sample_page,
                object_type="checkbox",
                content=json.dumps({"text": f"Task {i}", "checked": False}),
            )
            page_object_repo.create(obj)
        objects = page_object_repo.get_by_page(sample_page)
        assert len(objects) == 3


class TestPageObjectRepoRead:
    def test_get_by_page_returns_objects(self, page_object_repo, sample_page):
        obj = PageObject(
            page_id=sample_page,
            object_type="checkbox",
            content=json.dumps({"text": "Task", "checked": False}),
        )
        page_object_repo.create(obj)
        objects = page_object_repo.get_by_page(sample_page)
        assert len(objects) == 1
        assert objects[0].object_type == "checkbox"

    def test_get_by_id_returns_object(self, page_object_repo, sample_page):
        obj = PageObject(
            page_id=sample_page,
            object_type="checkbox",
            content=json.dumps({"text": "Task", "checked": False}),
        )
        obj_id = page_object_repo.create(obj)
        found = page_object_repo.get_by_id(obj_id)
        assert found is not None
        assert found.id == obj_id

    def test_get_by_id_returns_none_for_nonexistent(self, page_object_repo):
        found = page_object_repo.get_by_id(99999)
        assert found is None


class TestPageObjectRepoUpdate:
    def test_updates_object(self, page_object_repo, sample_page):
        obj = PageObject(
            page_id=sample_page,
            object_type="checkbox",
            content=json.dumps({"text": "Task", "checked": False}),
        )
        obj_id = page_object_repo.create(obj)
        found = page_object_repo.get_by_id(obj_id)
        found.is_checked = True
        found.content = json.dumps({"text": "Task", "checked": True})
        page_object_repo.update(found)
        updated = page_object_repo.get_by_id(obj_id)
        assert updated.is_checked


class TestPageObjectRepoDelete:
    def test_deletes_object(self, page_object_repo, sample_page):
        obj = PageObject(
            page_id=sample_page,
            object_type="checkbox",
            content=json.dumps({"text": "Task", "checked": False}),
        )
        obj_id = page_object_repo.create(obj)
        page_object_repo.delete(obj_id)
        found = page_object_repo.get_by_id(obj_id)
        assert found is None

    def test_deletes_by_page(self, page_object_repo, sample_page):
        for i in range(3):
            obj = PageObject(
                page_id=sample_page,
                object_type="checkbox",
                content=json.dumps({"text": f"Task {i}", "checked": False}),
            )
            page_object_repo.create(obj)
        page_object_repo.delete_by_page(sample_page)
        objects = page_object_repo.get_by_page(sample_page)
        assert len(objects) == 0
