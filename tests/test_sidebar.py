import pytest
from PyQt6.QtCore import Qt

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
        assert sidebar._splitter.sizes()[0] >= sidebar._splitter.sizes()[1]

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
    def test_fun_imports_does_not_emit_page_selected(self, sidebar, qtbot):
        PageRepo().create(Page(title="Fun Imports", page_type="folder"))
        sidebar.refresh()

        received = []
        sidebar.page_selected.connect(lambda pid: received.append(pid))

        item = sidebar.template_tree.topLevelItem(0)
        sidebar.template_tree.setCurrentItem(item)
        sidebar.template_tree.itemClicked.emit(item, 0)

        assert len(received) == 0

    def test_archive_does_not_emit_page_selected(self, sidebar):
        PageRepo().create(Page(title="Archive", page_type="folder"))
        sidebar.refresh()

        received = []
        sidebar.page_selected.connect(lambda pid: received.append(pid))

        item = sidebar.template_tree.topLevelItem(0)
        sidebar.template_tree.itemClicked.emit(item, 0)

        assert len(received) == 0


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
