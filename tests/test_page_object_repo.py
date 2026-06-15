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


class TestPageObjectRepoCopy:
    def test_copy_objects_to_empty_page(self, sample_page):
        src_id = PageRepo().create(Page(title="Source"))
        for i in range(3):
            PageObjectRepo.create(
                PageObject(
                    page_id=src_id,
                    object_type="checkbox",
                    content=json.dumps({"text": f"Task {i}"}),
                    sort_order=i * 100 + 50,
                )
            )
        dest_id = PageRepo().create(Page(title="Dest"))
        count = PageObjectRepo.copy_objects(src_id, dest_id)
        assert count == 3
        dest_objs = PageObjectRepo.get_by_page(dest_id)
        assert len(dest_objs) == 3

    def test_copy_objects_clears_destination_first(self, sample_page):
        src_id = PageRepo().create(Page(title="Source"))
        PageObjectRepo.create(
            PageObject(
                page_id=src_id,
                object_type="textbox_meta",
                content=json.dumps({"x": 100, "y": 200}),
                sort_order=150,
            )
        )
        dest_id = PageRepo().create(Page(title="Dest"))
        PageObjectRepo.create(
            PageObject(
                page_id=dest_id,
                object_type="textbox_meta",
                content=json.dumps({"x": 50, "y": 50}),
                sort_order=150,
            )
        )
        PageObjectRepo.copy_objects(src_id, dest_id)
        dest_objs = PageObjectRepo.get_by_page(dest_id)
        metas = [o for o in dest_objs if o.object_type == "textbox_meta"]
        assert len(metas) == 1
        data = json.loads(metas[0].content)
        assert data["x"] == 100

    def test_copy_objects_preserves_content_positions(self, sample_page):
        src_id = PageRepo().create(Page(title="Source"))
        PageObjectRepo.create(
            PageObject(
                page_id=src_id,
                object_type="textbox_meta",
                content=json.dumps({"x": 300, "y": 400, "width": 500}),
                sort_order=150,
            )
        )
        dest_id = PageRepo().create(Page(title="Dest"))
        PageObjectRepo.copy_objects(src_id, dest_id)
        dest_objs = PageObjectRepo.get_by_page(dest_id)
        meta = [o for o in dest_objs if o.object_type == "textbox_meta"][0]
        data = json.loads(meta.content)
        assert data["x"] == 300
        assert data["y"] == 400
        assert data["width"] == 500

    def test_copy_objects_preserves_sort_order_grouping(self, sample_page):
        src_id = PageRepo().create(Page(title="Source"))
        PageObjectRepo.create(
            PageObject(
                page_id=src_id,
                object_type="checklist_meta",
                content=json.dumps({"x": 0, "y": 0}),
                sort_order=50,
            )
        )
        PageObjectRepo.create(
            PageObject(
                page_id=src_id,
                object_type="checkbox",
                content=json.dumps({"text": "Item"}),
                sort_order=0,
            )
        )
        dest_id = PageRepo().create(Page(title="Dest"))
        PageObjectRepo.copy_objects(src_id, dest_id)
        dest_objs = PageObjectRepo.get_by_page(dest_id)
        meta = [o for o in dest_objs if o.object_type == "checklist_meta"][0]
        item = [o for o in dest_objs if o.object_type == "checkbox"][0]
        assert meta.sort_order == 50
        assert item.sort_order == 0
        assert meta.sort_order // 100 == item.sort_order // 100

    def test_template_full_flow_save_then_import(self, sample_page):
        """Simulate: create page with objects -> save as template -> import template."""
        original_id = PageRepo().create(Page(title="Daily Page"))
        PageObjectRepo.create(
            PageObject(
                page_id=original_id,
                object_type="textbox_meta",
                content=json.dumps({"x": 100, "y": 200, "width": 500, "height": 300}),
                sort_order=150,
            )
        )
        PageObjectRepo.create(
            PageObject(
                page_id=original_id,
                object_type="checklist_meta",
                content=json.dumps({"x": 50, "y": 50, "width": 400}),
                sort_order=50,
            )
        )
        PageObjectRepo.create(
            PageObject(
                page_id=original_id,
                object_type="checkbox",
                content=json.dumps({"text": "Task 1"}),
                sort_order=0,
            )
        )

        templates_id = PageRepo().create(Page(title="Templates", page_type="folder"))
        template_page = PageRepo().create(
            Page(
                title="Daily Page",
                parent_id=templates_id,
                page_type="template_page",
            )
        )
        count = PageObjectRepo.copy_objects(original_id, template_page)
        assert count == 3
        tpl_objs = PageObjectRepo.get_by_page(template_page)
        assert len(tpl_objs) == 3

        dest_id = PageRepo().create(Page(title="New Page"))
        count = PageObjectRepo.copy_objects(template_page, dest_id)
        assert count == 3
        dest_objs = PageObjectRepo.get_by_page(dest_id)
        assert len(dest_objs) == 3

        tb_meta = [o for o in dest_objs if o.object_type == "textbox_meta"][0]
        tb_data = json.loads(tb_meta.content)
        assert tb_data["x"] == 100
        assert tb_data["y"] == 200
        assert tb_data["width"] == 500

        cl_meta = [o for o in dest_objs if o.object_type == "checklist_meta"][0]
        cl_data = json.loads(cl_meta.content)
        assert cl_data["x"] == 50
        assert cl_data["y"] == 50

    def test_template_import_into_page_with_existing_objects(self, sample_page):
        """Import template into a page that already has objects."""
        original_id = PageRepo().create(Page(title="Template Page"))
        PageObjectRepo.create(
            PageObject(
                page_id=original_id,
                object_type="textbox_meta",
                content=json.dumps({"x": 100, "y": 200}),
                sort_order=150,
            )
        )

        templates_id = PageRepo().create(Page(title="Templates", page_type="folder"))
        template_page = PageRepo().create(
            Page(
                title="Template Page",
                parent_id=templates_id,
                page_type="template_page",
            )
        )
        PageObjectRepo.copy_objects(original_id, template_page)

        dest_id = PageRepo().create(Page(title="Existing Page"))
        PageObjectRepo.create(
            PageObject(
                page_id=dest_id,
                object_type="textbox_meta",
                content=json.dumps({"x": 999, "y": 999}),
                sort_order=150,
            )
        )

        count = PageObjectRepo.copy_objects(template_page, dest_id)
        assert count == 1
        dest_objs = PageObjectRepo.get_by_page(dest_id)
        assert len(dest_objs) == 1
        meta = dest_objs[0]
        data = json.loads(meta.content)
        assert data["x"] == 100
        assert data["y"] == 200
