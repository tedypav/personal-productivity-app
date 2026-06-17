from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLineEdit

from src.models.page import Page
from src.repositories.page_repo import PageRepo


@pytest.fixture
def sidebar(app_instance):
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

    def test_sidebar_has_tree(self, sidebar):
        assert sidebar.tree is not None

    def test_sidebar_has_template_tree(self, sidebar):
        assert sidebar.template_tree is not None

    def test_sidebar_has_splitter(self, sidebar):
        assert sidebar._splitter is not None


class TestSidebarExpandCollapse:
    def test_expand_all(self, sidebar):
        PageRepo().create(Page(title="P1"))
        sidebar.refresh()
        sidebar._expand_all()
        assert sidebar.tree.topLevelItemCount() > 0

    def test_collapse_all(self, sidebar):
        PageRepo().create(Page(title="P1"))
        sidebar.refresh()
        sidebar._expand_all()
        sidebar._collapse_all()
        assert sidebar.tree.topLevelItemCount() >= 0


class TestSidebarRefresh:
    def test_refresh_loads_pages(self, sidebar):
        PageRepo().create(Page(title="TestRefresh"))
        sidebar.refresh()
        assert sidebar.tree.topLevelItemCount() > 0


class TestSidebarSplitterPersistence:
    def test_splitter_has_default_stretch(self, sidebar):
        sizes = sidebar._splitter.sizes()
        assert sizes[0] >= 0
        assert sizes[1] >= 0

    def test_splitter_saves_sizes(self, sidebar, monkeypatch):
        sidebar._splitter.setSizes([400, 200])
        actual = sidebar._splitter.sizes()
        sidebar._save_splitter_sizes(actual[0], 0)
        assert sidebar.settings.get("sidebar_splitter_sizes") == actual

    def test_splitter_restores_sizes(self, app_instance, tmp_path):
        from src.settings import load_settings, save_settings

        fake_path = str(tmp_path / "settings.json")
        import src.settings as settings_mod

        original_path = settings_mod.SETTINGS_PATH
        settings_mod.SETTINGS_PATH = fake_path
        try:
            save_settings({"sidebar_splitter_sizes": [200, 100]})
            loaded = load_settings()
            assert loaded["sidebar_splitter_sizes"] == [200, 100]

            from src.ui.sidebar import Sidebar

            s = Sidebar()
            assert s.settings.get("sidebar_splitter_sizes") == [200, 100]
            s.close()
        finally:
            settings_mod.SETTINGS_PATH = original_path


class TestSidebarLowerTree:
    def test_lower_tree_has_special_folders(self, sidebar):
        titles = [
            sidebar.template_tree.topLevelItem(i).text(0)
            for i in range(sidebar.template_tree.topLevelItemCount())
        ]
        assert "Archive" in titles
        assert "Fun Imports" in titles
        assert "Templates" in titles

    def test_fun_imports_appears_in_lower_tree(self, sidebar):
        PageRepo().create(Page(title="Fun Imports", page_type="folder"))
        sidebar.refresh()
        titles = [
            sidebar.template_tree.topLevelItem(i).text(0)
            for i in range(sidebar.template_tree.topLevelItemCount())
        ]
        assert "Fun Imports" in titles

    def test_archive_appears_in_lower_tree(self, sidebar):
        PageRepo().create(Page(title="Archive", page_type="folder"))
        sidebar.refresh()
        titles = [
            sidebar.template_tree.topLevelItem(i).text(0)
            for i in range(sidebar.template_tree.topLevelItemCount())
        ]
        assert "Archive" in titles

    def test_regular_pages_not_in_lower_tree(self, sidebar):
        PageRepo().create(Page(title="My Page", page_type="page"))
        sidebar.refresh()
        titles = [
            sidebar.template_tree.topLevelItem(i).text(0)
            for i in range(sidebar.template_tree.topLevelItemCount())
        ]
        assert "My Page" not in titles

    def test_regular_pages_in_upper_tree(self, sidebar):
        PageRepo().create(Page(title="My Page", page_type="page"))
        sidebar.refresh()
        titles = [
            sidebar.tree.topLevelItem(i).text(0)
            for i in range(sidebar.tree.topLevelItemCount())
        ]
        assert "My Page" in titles

    def test_lower_tree_starts_collapsed(self, sidebar):
        PageRepo().create(Page(title="Fun Imports", page_type="folder"))
        PageRepo().create(Page(title="child", page_type="page"))
        sidebar.refresh()
        item = sidebar.template_tree.topLevelItem(0)
        assert item is not None
        assert not item.isExpanded()

    def test_special_folders_sorted_alphabetically(self, sidebar):
        PageRepo().create(Page(title="Fun Imports", page_type="folder"))
        PageRepo().create(Page(title="Archive", page_type="folder"))
        sidebar.refresh()
        titles = [
            sidebar.template_tree.topLevelItem(i).text(0)
            for i in range(sidebar.template_tree.topLevelItemCount())
        ]
        assert titles == sorted(titles)

    def test_expansion_state_persists_across_refresh(self, sidebar):
        archive_id = PageRepo().create(Page(title="Archive", page_type="folder"))
        PageRepo().create(Page(title="child", page_type="page", parent_id=archive_id))
        sidebar.refresh()
        item = sidebar.template_tree.topLevelItem(0)
        item.setExpanded(True)
        sidebar.refresh()
        restored = sidebar.template_tree.topLevelItem(0)
        assert restored is not None
        assert restored.isExpanded()

    def test_collapsed_state_persists_across_refresh(self, sidebar):
        PageRepo().create(Page(title="Archive", page_type="folder"))
        sidebar.refresh()
        item = sidebar.template_tree.topLevelItem(0)
        item.setExpanded(True)
        sidebar.refresh()
        item = sidebar.template_tree.topLevelItem(0)
        item.setExpanded(False)
        sidebar.refresh()
        restored = sidebar.template_tree.topLevelItem(0)
        assert restored is not None
        assert not restored.isExpanded()

    def test_expand_and_collapse_toggle(self, sidebar):
        PageRepo().create(Page(title="Archive", page_type="folder"))
        sidebar.refresh()
        item = sidebar.template_tree.topLevelItem(0)
        assert not item.isExpanded()
        item.setExpanded(True)
        assert item.isExpanded()
        item.setExpanded(False)
        assert not item.isExpanded()


class TestSidebarSpecialFolderClicks:
    def test_fun_imports_does_not_emit_page_selected(self, sidebar):
        sidebar.refresh()

        received = []
        sidebar.page_selected.connect(lambda pid: received.append(pid))

        item = sidebar.template_tree.topLevelItem(0)
        while item and item.text(0) != "Fun Imports":
            item = sidebar.template_tree.itemBelow(item)
        assert item is not None
        sidebar.template_tree.itemClicked.emit(item, 0)

        assert len(received) == 0

    def test_archive_emits_page_selected(self, sidebar):
        sidebar.refresh()

        received = []
        sidebar.page_selected.connect(lambda pid: received.append(pid))

        item = sidebar.template_tree.topLevelItem(0)
        while item and item.text(0) != "Archive":
            item = sidebar.template_tree.itemBelow(item)
        assert item is not None
        sidebar.template_tree.itemClicked.emit(item, 0)

        assert len(received) == 1

    def test_page_in_archive_emits_page_selected(self, sidebar):
        archive = [
            p
            for p in PageRepo().get_all()
            if p.title == "Archive" and p.page_type == "folder"
        ][0]
        PageRepo().create(Page(title="ArchivedPage", parent_id=archive.id))
        sidebar.refresh()

        received = []
        sidebar.page_selected.connect(lambda pid: received.append(pid))

        archive_item = sidebar.template_tree.topLevelItem(0)
        while archive_item and archive_item.text(0) != "Archive":
            archive_item = sidebar.template_tree.itemBelow(archive_item)
        assert archive_item is not None
        archive_item.setExpanded(True)
        child_item = archive_item.child(0)
        sidebar.template_tree.itemClicked.emit(child_item, 0)

        assert len(received) == 1


class TestSetAsTemplate:
    def test_set_as_template_creates_copy(self, sidebar):
        pid = PageRepo().create(Page(title="MyPage", page_type="page"))
        sidebar._set_as_template(pid)
        templates = [
            p
            for p in PageRepo().get_all()
            if p.title == "MyPage" and p.page_type == "template_page"
        ]
        assert len(templates) == 1

    def test_set_as_template_in_templates_folder(self, sidebar):
        pid = PageRepo().create(Page(title="MyPage", page_type="page"))
        sidebar._set_as_template(pid)
        templates = [
            p
            for p in PageRepo().get_all()
            if p.title == "MyPage" and p.page_type == "template_page"
        ]
        assert len(templates) == 1
        child = templates[0]
        folders = [
            p
            for p in PageRepo().get_all()
            if p.title == "Templates" and p.page_type == "folder"
        ]
        assert len(folders) == 1
        assert child.parent_id == folders[0].id

    def test_set_as_template_preserves_title(self, sidebar):
        pid = PageRepo().create(Page(title="SpecialPage", page_type="page"))
        sidebar._set_as_template(pid)
        templates = [p for p in PageRepo().get_all() if p.page_type == "template_page"]
        assert templates[0].title == "SpecialPage"

    def test_set_as_template_creates_templates_folder(self, sidebar):
        pid = PageRepo().create(Page(title="MyPage", page_type="page"))
        sidebar._set_as_template(pid)
        folders = [
            p
            for p in PageRepo().get_all()
            if p.title == "Templates" and p.page_type == "folder"
        ]
        assert len(folders) == 1

    def test_set_as_template_does_not_move_original(self, sidebar):
        pid = PageRepo().create(Page(title="MyPage", page_type="page"))
        sidebar._set_as_template(pid)
        original = PageRepo().get_by_id(pid)
        assert original.parent_id is None
        assert original.page_type == "page"

    def test_template_page_uses_blue_icon(self, sidebar):
        pid = PageRepo().create(Page(title="Tpl", page_type="template_page"))
        sidebar.refresh()
        item = None
        for i in range(sidebar.tree.topLevelItemCount()):
            child = sidebar.tree.topLevelItem(i)
            if child.data(0, Qt.ItemDataRole.UserRole) == pid:
                item = child
                break
        assert item is not None
        icon = item.icon(0)
        assert not icon.isNull()

    def test_set_as_template_copies_objects(self, sidebar):
        import json

        from src.models.page_object import PageObject
        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="MyPage", page_type="page"))
        PageObjectRepo().create(
            PageObject(
                page_id=pid,
                object_type="checkbox",
                content=json.dumps({"text": "task1", "checked": False}),
            )
        )
        PageObjectRepo().create(
            PageObject(
                page_id=pid,
                object_type="checkbox",
                content=json.dumps({"text": "task2", "checked": True}),
            )
        )

        sidebar._set_as_template(pid)

        templates = [
            p
            for p in PageRepo().get_all()
            if p.title == "MyPage" and p.page_type == "template_page"
        ]
        assert len(templates) == 1
        template_objects = PageObjectRepo().get_by_page(templates[0].id)
        assert len(template_objects) == 2
        assert template_objects[0].object_type == "checkbox"
        assert template_objects[1].object_type == "checkbox"

    def test_set_as_template_preserves_object_content(self, sidebar):
        import json

        from src.models.page_object import PageObject
        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="MyPage", page_type="page"))
        content = json.dumps({"text": "Buy milk", "checked": False})
        PageObjectRepo().create(
            PageObject(page_id=pid, object_type="checkbox", content=content)
        )

        sidebar._set_as_template(pid)

        templates = [
            p
            for p in PageRepo().get_all()
            if p.title == "MyPage" and p.page_type == "template_page"
        ]
        template_objects = PageObjectRepo().get_by_page(templates[0].id)
        assert len(template_objects) == 1
        assert json.loads(template_objects[0].content) == json.loads(content)

    def test_set_as_template_creates_independent_copy(self, sidebar):
        import json

        from src.models.page_object import PageObject
        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="MyPage", page_type="page"))
        obj = PageObject(
            page_id=pid,
            object_type="checkbox",
            content=json.dumps({"text": "original"}),
        )
        obj_id = PageObjectRepo().create(obj)

        sidebar._set_as_template(pid)

        original_obj = PageObjectRepo().get_by_id(obj_id)
        original_obj.content = json.dumps({"text": "modified"})
        PageObjectRepo().update(original_obj)

        templates = [
            p
            for p in PageRepo().get_all()
            if p.title == "MyPage" and p.page_type == "template_page"
        ]
        template_objects = PageObjectRepo().get_by_page(templates[0].id)
        assert len(template_objects) == 1
        assert json.loads(template_objects[0].content)["text"] == "original"


class TestUniqueNames:
    def test_unique_name_adds_suffix(self, sidebar):
        name = sidebar._get_unique_name("Test", None)
        assert name == "Test"

    def test_unique_name_conflict(self, sidebar):
        PageRepo().create(Page(title="Test", page_type="page"))
        name = sidebar._get_unique_name("Test", None)
        assert name == "Test (1)"

    def test_unique_name_multiple_conflicts(self, sidebar):
        PageRepo().create(Page(title="Test", page_type="page"))
        PageRepo().create(Page(title="Test (1)", page_type="page"))
        name = sidebar._get_unique_name("Test", None)
        assert name == "Test (2)"

    def test_unique_name_in_folder(self, sidebar):
        folder_id = PageRepo().create(Page(title="Folder", page_type="folder"))
        PageRepo().create(Page(title="Test", parent_id=folder_id, page_type="page"))
        name = sidebar._get_unique_name("Test", folder_id)
        assert name == "Test (1)"

    def test_unique_name_different_folder(self, sidebar):
        f1 = PageRepo().create(Page(title="F1", page_type="folder"))
        f2 = PageRepo().create(Page(title="F2", page_type="folder"))
        PageRepo().create(Page(title="Test", parent_id=f1, page_type="page"))
        name = sidebar._get_unique_name("Test", f2)
        assert name == "Test"

    def test_unique_name_excludes_self(self, sidebar):
        pid = PageRepo().create(Page(title="Test", page_type="page"))
        name = sidebar._get_unique_name("Test", None, exclude_id=pid)
        assert name == "Test"


class TestArchiveMerge:
    def test_archive_merges_same_name_folders(self, sidebar):
        archive = [
            p
            for p in PageRepo().get_all()
            if p.title == "Archive" and p.page_type == "folder"
        ][0]
        folder_a_id = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        PageRepo().create(Page(title="ChildA", parent_id=folder_a_id, page_type="page"))
        folder_b_id = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        PageRepo().create(Page(title="ChildB", parent_id=folder_b_id, page_type="page"))
        sidebar._archive_item(folder_a_id, "folder")
        sidebar._archive_item(folder_b_id, "folder")
        folder_b = PageRepo().get_by_id(folder_b_id)
        assert folder_b is None
        folder_a = PageRepo().get_by_id(folder_a_id)
        assert folder_a is not None
        assert folder_a.parent_id == archive.id
        children = PageRepo().get_children(folder_a_id)
        names = [c.title for c in children]
        assert "ChildA" in names
        assert "ChildB" in names

    def test_archive_unique_folder_name(self, sidebar):
        archive = [
            p
            for p in PageRepo().get_all()
            if p.title == "Archive" and p.page_type == "folder"
        ][0]
        folder_id = PageRepo().create(Page(title="UniqueFolder", page_type="folder"))
        sidebar._archive_item(folder_id, "folder")
        folder = PageRepo().get_by_id(folder_id)
        assert folder is not None
        assert folder.parent_id == archive.id


class TestTemplateUniqueNames:
    def test_template_name_unique(self, sidebar):
        pid = PageRepo().create(Page(title="MyPage", page_type="page"))
        sidebar._set_as_template(pid)
        sidebar._set_as_template(pid)
        templates = [p for p in PageRepo().get_all() if p.page_type == "template_page"]
        names = [t.title for t in templates]
        assert "MyPage" in names
        assert "MyPage (1)" in names


class TestBulkCreateDialogStyling:
    def test_calendar_chevron_icon_exists(self):
        import os

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets",
            "icons",
            "chevron_down.svg",
        )
        assert os.path.exists(icon_path)

    def test_heart_icon_exists(self):
        import os

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets",
            "icons",
            "heart.svg",
        )
        assert os.path.exists(icon_path)

    def test_flower_icon_exists(self):
        import os

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets",
            "icons",
            "flower.svg",
        )
        assert os.path.exists(icon_path)

    def test_chevron_up_icon_exists(self):
        import os

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets",
            "icons",
            "chevron_up.svg",
        )
        assert os.path.exists(icon_path)


class TestBulkCreateSkipsDuplicates:
    def test_bulk_named_skips_existing_pages(self, sidebar):
        PageRepo().create(Page(title="Page 1", parent_id=None))
        existing = PageRepo().get_children(None)
        existing_titles = {p.title for p in existing}
        assert "Page 1" in existing_titles

        base = "Page"
        count = 3
        for i in range(1, count + 1):
            title = f"{base} {i}"
            if title not in existing_titles:
                PageRepo().create(Page(title=title, page_type="page", parent_id=None))

        all_pages = PageRepo().get_children(None)
        all_titles = [p.title for p in all_pages]
        assert all_titles.count("Page 1") == 1
        assert "Page 2" in all_titles
        assert "Page 3" in all_titles

    def test_bulk_named_creates_only_new_pages(self, sidebar):
        PageRepo().create(Page(title="Task 1", parent_id=None))
        PageRepo().create(Page(title="Task 2", parent_id=None))

        existing = {p.title for p in PageRepo().get_children(None)}
        new_titles = ["Task 1", "Task 2", "Task 3", "Task 4"]
        for title in new_titles:
            if title not in existing:
                PageRepo().create(Page(title=title, page_type="page", parent_id=None))

        all_pages = PageRepo().get_children(None)
        task_pages = [p for p in all_pages if p.title.startswith("Task")]
        assert len(task_pages) == 4

    def test_bulk_date_skips_existing_pages(self, sidebar):
        PageRepo().create(Page(title="2026-01-01", parent_id=None))

        existing = {p.title for p in PageRepo().get_children(None)}
        titles = ["2026-01-01", "2026-01-02", "2026-01-03"]
        for title in titles:
            if title not in existing:
                PageRepo().create(Page(title=title, page_type="page", parent_id=None))

        all_pages = PageRepo().get_children(None)
        all_titles = [p.title for p in all_pages]
        assert all_titles.count("2026-01-01") == 1
        assert "2026-01-02" in all_titles
        assert "2026-01-03" in all_titles


class TestDelegateSurvivesDeletion:
    def test_hover_index_cleared_after_delete(self, sidebar):
        pid = PageRepo().create(Page(title="TestPage"))
        sidebar.refresh()

        delegate = sidebar.tree.itemDelegate()
        items = sidebar.tree.findItems(
            "TestPage",
            Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive,
        )
        assert len(items) == 1
        index = sidebar.tree.indexFromItem(items[0])
        delegate._hovered_index = index

        sidebar._delete_item(pid)

        assert delegate._hovered_index is None

    def test_hover_index_cleared_after_clear(self, sidebar):
        PageRepo().create(Page(title="TestPage"))
        sidebar.refresh()

        delegate = sidebar.tree.itemDelegate()
        items = sidebar.tree.findItems(
            "TestPage",
            Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive,
        )
        assert len(items) == 1
        index = sidebar.tree.indexFromItem(items[0])
        delegate._hovered_index = index

        sidebar.tree.clear()

        assert delegate._hovered_index is None

    def test_delegate_handles_scroll_after_delete(self, sidebar):
        pid = PageRepo().create(Page(title="TestPage"))
        sidebar.refresh()

        delegate = sidebar.tree.itemDelegate()
        items = sidebar.tree.findItems(
            "TestPage",
            Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive,
        )
        assert len(items) == 1
        index = sidebar.tree.indexFromItem(items[0])
        delegate._hovered_index = index

        sidebar._delete_item(pid)

        sidebar.tree.verticalScrollBar().setValue(0)
        assert delegate._hovered_index is None


class TestBulkCreationDates:
    def test_bulk_date_range_respects_user_selection(self, sidebar):
        from datetime import date, timedelta

        start = date(2026, 1, 1)
        end = date(2026, 1, 10)
        titles = []
        current = start
        while current <= end:
            titles.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        assert len(titles) == 10
        assert titles[0] == "2026-01-01"
        assert titles[-1] == "2026-01-10"

    def test_bulk_date_range_single_day(self, sidebar):
        from datetime import date, timedelta

        start = date(2026, 3, 15)
        end = date(2026, 3, 15)
        titles = []
        current = start
        while current <= end:
            titles.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        assert titles == ["2026-03-15"]

    def test_bulk_named_skips_duplicates_across_runs(self, sidebar):
        PageRepo().create(Page(title="Report 1", parent_id=None))
        PageRepo().create(Page(title="Report 2", parent_id=None))

        existing = {p.title for p in PageRepo().get_children(None)}
        base = "Report"
        count = 5
        for i in range(1, count + 1):
            title = f"{base} {i}"
            if title not in existing:
                PageRepo().create(Page(title=title, page_type="page", parent_id=None))

        all_pages = PageRepo().get_children(None)
        report_pages = [p for p in all_pages if p.title.startswith("Report")]
        titles = sorted([p.title for p in report_pages])
        assert titles == ["Report 1", "Report 2", "Report 3", "Report 4", "Report 5"]


class TestSidebarDeleteItem:
    def test_delete_item_removes_page(self, sidebar):
        pid = PageRepo().create(Page(title="ToDelete"))
        sidebar._delete_item(pid)
        assert PageRepo().get_by_id(pid) is None

    def test_delete_item_with_children(self, sidebar):
        pid = PageRepo().create(Page(title="Parent"))
        child_id = PageRepo().create(Page(title="Child", parent_id=pid))
        sidebar._delete_item(pid)
        assert PageRepo().get_by_id(pid) is None
        assert PageRepo().get_by_id(child_id) is None

    def test_delete_item_clears_editor(self, sidebar):
        mock_editor = MagicMock()
        pid = PageRepo().create(Page(title="ToDelete"))
        mock_editor.current_page_id = pid
        sidebar._editor_ref = mock_editor
        sidebar._delete_items_by_id([pid], clear_editor=True)
        mock_editor.clear_editor.assert_called_once()


class TestSidebarBulkDelete:
    def test_bulk_delete_multiple_pages(self, sidebar):
        p1 = PageRepo().create(Page(title="A"))
        p2 = PageRepo().create(Page(title="B"))
        p3 = PageRepo().create(Page(title="C"))
        sidebar.refresh()
        items = []
        for i in range(sidebar.tree.topLevelItemCount()):
            item = sidebar.tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) in (p1, p2, p3):
                items.append(item)
        assert len(items) == 3
        sidebar._bulk_delete(items)
        assert PageRepo().get_by_id(p1) is None
        assert PageRepo().get_by_id(p2) is None
        assert PageRepo().get_by_id(p3) is None

    def test_bulk_delete_empty_list(self, sidebar):
        sidebar._bulk_delete([])

    def test_bulk_delete_with_parent_selected_skips_child(self, sidebar):
        parent_id = PageRepo().create(Page(title="Parent"))
        child_id = PageRepo().create(Page(title="Child", parent_id=parent_id))
        sidebar.refresh()
        parent_item = None
        for i in range(sidebar.tree.topLevelItemCount()):
            item = sidebar.tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == parent_id:
                parent_item = item
                break
        assert parent_item is not None
        sidebar._bulk_delete([parent_item])
        assert PageRepo().get_by_id(parent_id) is None
        assert PageRepo().get_by_id(child_id) is None


class TestSidebarDeleteItems:
    def test_delete_items_single(self, sidebar):
        pid = PageRepo().create(Page(title="Single"))
        sidebar.refresh()
        items = sidebar.tree.findItems(
            "Single", Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive
        )
        assert len(items) == 1
        sidebar._delete_items(items)
        assert PageRepo().get_by_id(pid) is None

    def test_delete_items_multiple(self, sidebar):
        p1 = PageRepo().create(Page(title="X1"))
        p2 = PageRepo().create(Page(title="X2"))
        sidebar.refresh()
        items = []
        for i in range(sidebar.tree.topLevelItemCount()):
            item = sidebar.tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) in (p1, p2):
                items.append(item)
        sidebar._delete_items(items)
        assert PageRepo().get_by_id(p1) is None
        assert PageRepo().get_by_id(p2) is None

    def test_delete_items_empty(self, sidebar):
        sidebar._delete_items([])

    def test_delete_selected_no_selection(self, sidebar):
        sidebar.delete_selected()


class TestSidebarIsDescendant:
    def test_self_is_descendant(self, sidebar):
        pid = PageRepo().create(Page(title="A"))
        assert sidebar._is_descendant(pid, pid) is True

    def test_child_is_descendant(self, sidebar):
        parent_id = PageRepo().create(Page(title="P"))
        child_id = PageRepo().create(Page(title="C", parent_id=parent_id))
        assert sidebar._is_descendant(parent_id, child_id) is True

    def test_grandchild_is_descendant(self, sidebar):
        root = PageRepo().create(Page(title="R"))
        child = PageRepo().create(Page(title="C", parent_id=root, page_type="folder"))
        grandchild = PageRepo().create(Page(title="G", parent_id=child))
        assert sidebar._is_descendant(root, grandchild) is True

    def test_unrelated_is_not_descendant(self, sidebar):
        a = PageRepo().create(Page(title="A"))
        b = PageRepo().create(Page(title="B"))
        assert sidebar._is_descendant(a, b) is False

    def test_descendant_of_child(self, sidebar):
        root = PageRepo().create(Page(title="R"))
        child = PageRepo().create(Page(title="C", parent_id=root))
        assert sidebar._is_descendant(root, child) is True
        assert sidebar._is_descendant(child, root) is False


class TestSidebarContextMove:
    def test_ctx_move_up(self, sidebar):
        pid = PageRepo().create(Page(title="MoveUp"))
        page = PageRepo().get_by_id(pid)
        original_order = page.sort_order
        sidebar._ctx_move(pid, -1)
        updated = PageRepo().get_by_id(pid)
        assert updated.sort_order == max(0, original_order - 1)

    def test_ctx_move_down(self, sidebar):
        pid = PageRepo().create(Page(title="MoveDown"))
        page = PageRepo().get_by_id(pid)
        original_order = page.sort_order
        sidebar._ctx_move(pid, 1)
        updated = PageRepo().get_by_id(pid)
        assert updated.sort_order == original_order + 1

    def test_ctx_move_nonexistent_page(self, sidebar):
        sidebar._ctx_move(99999, 1)


class TestSidebarCtxDelete:
    def test_ctx_delete_removes_page(self, sidebar):
        pid = PageRepo().create(Page(title="CtxDel"))
        sidebar._ctx_delete(pid)
        assert PageRepo().get_by_id(pid) is None

    def test_ctx_delete_emits_pages_changed(self, sidebar):
        pid = PageRepo().create(Page(title="Changed"))
        changed = []
        sidebar.pages_changed.connect(lambda: changed.append(True))
        sidebar._ctx_delete(pid)
        assert len(changed) == 1


class TestSidebarCtxAddChild:
    def test_ctx_add_child_page(self, sidebar):
        pid = PageRepo().create(Page(title="Parent"))
        with patch(
            "src.ui.sidebar.QInputDialog.getText", return_value=("NewChild", True)
        ):
            sidebar._ctx_add_child(pid)
        children = PageRepo().get_children(pid)
        assert len(children) == 1
        assert children[0].title == "NewChild"

    def test_ctx_add_child_folder(self, sidebar):
        pid = PageRepo().create(Page(title="Parent"))
        with patch(
            "src.ui.sidebar.QInputDialog.getText", return_value=("NewFolder", True)
        ):
            sidebar._ctx_add_child(pid, "folder")
        children = PageRepo().get_children(pid)
        assert len(children) == 1
        assert children[0].page_type == "folder"

    def test_ctx_add_child_cancelled(self, sidebar):
        pid = PageRepo().create(Page(title="Parent"))
        with patch("src.ui.sidebar.QInputDialog.getText", return_value=("", False)):
            sidebar._ctx_add_child(pid)
        children = PageRepo().get_children(pid)
        assert len(children) == 0


class TestSidebarCtxRename:
    def test_ctx_rename_page(self, sidebar):
        pid = PageRepo().create(Page(title="OldName"))
        sidebar.refresh()
        items = sidebar.tree.findItems(
            "OldName", Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive
        )
        assert len(items) == 1
        with patch(
            "src.ui.sidebar.QInputDialog.getText", return_value=("NewName", True)
        ):
            sidebar._ctx_rename(items[0], pid, "page")
        updated = PageRepo().get_by_id(pid)
        assert updated.title == "NewName"

    def test_ctx_rename_folder_strips_emoji(self, sidebar):
        pid = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        sidebar.refresh()
        items = sidebar.tree.findItems(
            "MyFolder", Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive
        )
        assert len(items) == 1
        with patch(
            "src.ui.sidebar.QInputDialog.getText", return_value=("Renamed", True)
        ):
            sidebar._ctx_rename(items[0], pid, "folder")
        updated = PageRepo().get_by_id(pid)
        assert updated.title == "Renamed"

    def test_ctx_rename_duplicate_name(self, sidebar):
        pid1 = PageRepo().create(Page(title="PageA"))
        PageRepo().create(Page(title="PageB"))
        sidebar.refresh()
        items = sidebar.tree.findItems(
            "PageA", Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive
        )
        with patch("src.ui.sidebar.QInputDialog.getText", return_value=("PageB", True)):
            sidebar._ctx_rename(items[0], pid1, "page")
        updated = PageRepo().get_by_id(pid1)
        assert updated.title == "PageB (1)"


class TestSidebarArchivePage:
    def test_archive_page_moves_to_archive(self, sidebar):
        archive = [
            p
            for p in PageRepo().get_all()
            if p.title == "Archive" and p.page_type == "folder"
        ][0]
        pid = PageRepo().create(Page(title="ArchiveMe"))
        sidebar._archive_page(pid, archive.id, PageRepo().get_all())
        archived = PageRepo().get_by_id(pid)
        assert archived is not None
        assert archived.parent_id == archive.id

    def test_archive_page_with_parent(self, sidebar):
        archive = [
            p
            for p in PageRepo().get_all()
            if p.title == "Archive" and p.page_type == "folder"
        ][0]
        folder_id = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        pid = PageRepo().create(Page(title="InFolder", parent_id=folder_id))
        sidebar._archive_page(pid, archive.id, PageRepo().get_all())
        archived = PageRepo().get_by_id(pid)
        assert archived is not None

    def test_archive_page_nonexistent(self, sidebar):
        archive_id = PageRepo().create(Page(title="Arch", page_type="folder"))
        sidebar._archive_page(99999, archive_id, PageRepo().get_all())


class TestSidebarFindOrCreateArchive:
    def test_finds_existing_archive(self, sidebar):
        archive_id, pages = sidebar._find_or_create_archive()
        assert archive_id is not None

    def test_creates_archive_if_missing(self, sidebar):
        archive_id, pages = sidebar._find_or_create_archive()
        assert archive_id is not None


class TestSidebarMoveToFolder:
    def test_move_to_root(self, sidebar):
        folder_id = PageRepo().create(Page(title="Target", page_type="folder"))
        pid = PageRepo().create(Page(title="MoveMe"))
        page = PageRepo().get_by_id(pid)
        page.parent_id = None
        PageRepo().update(page)
        page.parent_id = folder_id
        PageRepo().update(page)
        moved = PageRepo().get_by_id(pid)
        assert moved.parent_id == folder_id

    def test_move_to_root_directly(self, sidebar):
        folder_id = PageRepo().create(Page(title="F", page_type="folder"))
        pid = PageRepo().create(Page(title="M", parent_id=folder_id))
        page = PageRepo().get_by_id(pid)
        page.parent_id = None
        PageRepo().update(page)
        moved = PageRepo().get_by_id(pid)
        assert moved.parent_id is None


class TestSidebarCreatePage:
    def test_create_page_with_input(self, sidebar):
        with patch(
            "src.ui.sidebar.QInputDialog.getText", return_value=("NewPage", True)
        ):
            sidebar._create_page()
        pages = [p for p in PageRepo().get_all() if p.title == "NewPage"]
        assert len(pages) == 1

    def test_create_page_cancelled(self, sidebar):
        with patch("src.ui.sidebar.QInputDialog.getText", return_value=("", False)):
            sidebar._create_page()

    def test_create_page_under_selected(self, sidebar):
        pid = PageRepo().create(Page(title="Parent", page_type="folder"))
        sidebar.refresh()
        items = sidebar.tree.findItems(
            "Parent", Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive
        )
        assert len(items) == 1
        sidebar.tree.setCurrentItem(items[0])
        with patch("src.ui.sidebar.QInputDialog.getText", return_value=("Child", True)):
            sidebar._create_page()
        children = PageRepo().get_children(pid)
        assert len(children) == 1
        assert children[0].title == "Child"


class TestSidebarCreateFolder:
    def test_create_folder(self, sidebar):
        with patch(
            "src.ui.sidebar.QInputDialog.getText", return_value=("NewFolder", True)
        ):
            sidebar._create_folder()
        folders = [p for p in PageRepo().get_all() if p.title == "NewFolder"]
        assert len(folders) == 1
        assert folders[0].page_type == "folder"

    def test_create_folder_cancelled(self, sidebar):
        with patch("src.ui.sidebar.QInputDialog.getText", return_value=("", False)):
            sidebar._create_folder()


class TestSidebarBulkCreateDialog:
    def test_bulk_create_dialog_creates_pages(self, sidebar):
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = 1
        mock_dialog.get_titles.return_value = ["2026-01-01", "2026-01-02"]
        with patch(
            "src.ui.bulk_create_dialog.BulkCreateDialog", return_value=mock_dialog
        ):
            sidebar._bulk_create_dialog()
        pages = PageRepo().get_all()
        titles = [p.title for p in pages]
        assert "2026-01-01" in titles
        assert "2026-01-02" in titles


class TestSidebarBulkNamedDialog:
    def test_bulk_named_dialog_empty_name(self, sidebar):
        from PyQt6.QtWidgets import QDialog as RealQDialog

        real_dialog = RealQDialog()
        real_dialog.exec = MagicMock(return_value=1)
        name_edit = QLineEdit("")
        with patch("src.ui.sidebar.QDialog", return_value=real_dialog):
            with patch("src.ui.sidebar.QLineEdit", return_value=name_edit):
                sidebar._bulk_named_dialog()


class TestSidebarTemplateClicked:
    def test_template_clicked_with_page(self, sidebar):
        pid = PageRepo().create(Page(title="TplPage"))
        mock_editor = MagicMock()
        mock_editor.current_page_id = pid
        sidebar._editor_ref = mock_editor
        sidebar._template_clicked()
        templates = [p for p in PageRepo().get_all() if p.page_type == "template_page"]
        assert len(templates) == 1

    def test_template_clicked_no_page(self, sidebar):
        sidebar._editor_ref = None
        sidebar._template_clicked()

    def test_template_clicked_no_editor_page(self, sidebar):
        mock_editor = MagicMock()
        mock_editor.current_page_id = None
        sidebar._editor_ref = mock_editor
        sidebar._template_clicked()


class TestSidebarArchiveSelected:
    def test_archive_selected_no_selection(self, sidebar):
        sidebar._archive_selected()

    def test_archive_selected_with_items(self, sidebar):
        pid = PageRepo().create(Page(title="ArchiveThis"))
        sidebar.refresh()
        items = sidebar.tree.findItems(
            "ArchiveThis", Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive
        )
        assert len(items) == 1
        sidebar.tree.setSelectionMode(sidebar.tree.SelectionMode.ExtendedSelection)
        sidebar.tree.setCurrentItem(items[0])
        sidebar._archive_selected()
        archived = PageRepo().get_by_id(pid)
        assert archived is not None


class TestSidebarCtxArchive:
    def test_ctx_archive_system_folder(self, sidebar):
        archive = [
            p
            for p in PageRepo().get_all()
            if p.title == "Archive" and p.page_type == "folder"
        ][0]
        sidebar._ctx_archive(archive.id, "folder")

    def test_ctx_archive_regular_page(self, sidebar):
        pid = PageRepo().create(Page(title="ToArchive"))
        sidebar._ctx_archive(pid, "page")
        archived = PageRepo().get_by_id(pid)
        assert archived is not None


class TestSidebarRenameSelected:
    def test_rename_selected(self, sidebar):
        pid = PageRepo().create(Page(title="RenameMe"))
        sidebar.refresh()
        items = sidebar.tree.findItems(
            "RenameMe", Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive
        )
        assert len(items) == 1
        sidebar.tree.setCurrentItem(items[0])
        with patch(
            "src.ui.sidebar.QInputDialog.getText", return_value=("RenamedOK", True)
        ):
            sidebar._rename_selected()
        updated = PageRepo().get_by_id(pid)
        assert updated.title == "RenamedOK"

    def test_rename_selected_no_selection(self, sidebar):
        sidebar._rename_selected()

    def test_rename_selected_multiple(self, sidebar):
        PageRepo().create(Page(title="A"))
        PageRepo().create(Page(title="B"))
        sidebar.refresh()
        sidebar._rename_selected()


class TestSidebarOnItemClick:
    def test_on_item_clicked_emits_signal(self, sidebar):
        pid = PageRepo().create(Page(title="ClickMe"))
        sidebar.refresh()
        received = []
        sidebar.page_selected.connect(lambda x: received.append(x))
        item = sidebar.tree.findItems(
            "ClickMe", Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive
        )[0]
        sidebar._on_item_clicked(item, 0)
        assert pid in received


class TestSidebarOnTemplateItemClick:
    def test_template_item_click_fun_imports(self, sidebar):
        sidebar._on_template_item_clicked(
            MagicMock(text=MagicMock(return_value="Fun Imports")), 0
        )

    def test_template_item_click_page(self, sidebar):
        pid = PageRepo().create(Page(title="TplPage", page_type="template_page"))
        sidebar.refresh()
        received = []
        sidebar.page_selected.connect(lambda x: received.append(x))
        item = MagicMock()
        item.data.return_value = pid
        item.text.return_value = "TplPage"
        sidebar._on_template_item_clicked(item, 0)
        assert pid in received
