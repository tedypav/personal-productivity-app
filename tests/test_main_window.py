import json

import pytest

from src.models.page import Page
from src.repositories.page_repo import PageRepo


@pytest.fixture
def main_window(app_instance):
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

    def test_has_splitter(self, main_window):
        assert main_window._splitter is not None


class TestMainWindowMenus:
    def test_has_file_menu(self, main_window):
        menubar = main_window.menuBar()
        actions = [a.text() for a in menubar.actions()]
        assert any("File" in a for a in actions)

    def test_has_page_menu(self, main_window):
        menubar = main_window.menuBar()
        actions = [a.text() for a in menubar.actions()]
        assert any("Page" in a for a in actions)

    def test_has_edit_menu(self, main_window):
        menubar = main_window.menuBar()
        actions = [a.text() for a in menubar.actions()]
        assert any("Edit" in a for a in actions)

    def test_has_view_menu(self, main_window):
        menubar = main_window.menuBar()
        actions = [a.text() for a in menubar.actions()]
        assert any("View" in a for a in actions)


class TestMainWindowToggleSidebar:
    def test_toggle_sidebar(self, main_window):
        visible = main_window.sidebar.isVisible()
        main_window._toggle_sidebar()
        assert main_window.sidebar.isVisible() != visible


class TestMainWindowSplitterPersistence:
    def test_splitter_saves_sizes(self, main_window):
        main_window._splitter.setSizes([300, 900])
        actual = main_window._splitter.sizes()
        main_window._save_splitter_sizes(actual[0], 0)
        assert main_window.settings.get("main_splitter_sizes") == actual

    def test_splitter_restores_sizes(self, app_instance, tmp_path):
        from src.settings import save_settings

        fake_path = str(tmp_path / "settings.json")
        import src.settings as settings_mod

        original = settings_mod.SETTINGS_PATH
        settings_mod.SETTINGS_PATH = fake_path
        try:
            save_settings({"main_splitter_sizes": [350, 850]})
            from src.ui.main_window import MainWindow

            mw = MainWindow()
            mw.resize(1200, 800)
            mw.show()
            app_instance.processEvents()
            sizes = mw._splitter.sizes()
            assert sizes[0] > 0
            assert sizes[1] > 0
            mw.close()
        finally:
            settings_mod.SETTINGS_PATH = original


class TestMainWindowPageLoading:
    def test_load_page_updates_title(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        assert main_window.editor.page_title.text() == "TestPage"

    def test_clear_editor_resets_title(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor.clear_editor()
        assert main_window.editor.page_title.text() == "Select a page"

    def test_welcome_label_visible_initially(self, main_window):
        assert main_window.editor.welcome_label.isVisible()

    def test_welcome_label_hidden_on_page_load(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        assert not main_window.editor.welcome_label.isVisible()

    def test_welcome_label_shown_on_clear(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor.clear_editor()
        assert main_window.editor.welcome_label.isVisible()


class TestPageEmptyHint:
    def test_empty_hint_hidden_initially(self, main_window):
        assert not main_window.editor._page_empty_hint.isVisible()

    def test_empty_hint_shown_on_page_load(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        assert main_window.editor._page_empty_hint.isVisible()

    def test_empty_hint_hidden_on_clear(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor.clear_editor()
        assert not main_window.editor._page_empty_hint.isVisible()

    def test_empty_hint_text(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        assert "first object" in main_window.editor._page_empty_hint.text()

    def test_empty_hint_is_italic(self, main_window):
        style = main_window.editor._page_empty_hint.styleSheet()
        assert "italic" in style


class TestCanvasBackground:
    def test_canvas_has_photo_bg_initially(self, main_window):
        assert main_window.editor.content._show_photo_bg is True

    def test_canvas_solid_bg_on_page_load(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        assert main_window.editor.content._show_photo_bg is False

    def test_canvas_photo_bg_on_clear(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor.clear_editor()
        assert main_window.editor.content._show_photo_bg is True


class TestFolderTableOfContents:
    def test_folder_shows_toc(self, main_window):
        folder_id = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        PageRepo().create(Page(title="Child1", parent_id=folder_id))
        main_window.editor.load_page(folder_id)
        assert main_window.editor._toc_widget is not None
        assert main_window.editor._toc_widget.isVisible()

    def test_folder_toc_hidden_hint(self, main_window):
        folder_id = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        PageRepo().create(Page(title="Child1", parent_id=folder_id))
        main_window.editor.load_page(folder_id)
        assert not main_window.editor._page_empty_hint.isVisible()

    def test_empty_folder_shows_no_toc(self, main_window):
        folder_id = PageRepo().create(Page(title="EmptyFolder", page_type="folder"))
        main_window.editor.load_page(folder_id)
        assert main_window.editor._toc_widget is None

    def test_toc_cleared_on_clear(self, main_window):
        folder_id = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        PageRepo().create(Page(title="Child1", parent_id=folder_id))
        main_window.editor.load_page(folder_id)
        main_window.editor.clear_editor()
        assert main_window.editor._toc_widget is None

    def test_toc_replaced_on_new_folder(self, main_window):
        f1 = PageRepo().create(Page(title="Folder1", page_type="folder"))
        PageRepo().create(Page(title="A", parent_id=f1))
        f2 = PageRepo().create(Page(title="Folder2", page_type="folder"))
        PageRepo().create(Page(title="B", parent_id=f2))
        main_window.editor.load_page(f1)
        old_toc = main_window.editor._toc_widget
        main_window.editor.load_page(f2)
        assert main_window.editor._toc_widget is not None
        assert main_window.editor._toc_widget is not old_toc

    def test_navigate_to_page_signal(self, main_window):
        folder_id = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        child_id = PageRepo().create(Page(title="Child1", parent_id=folder_id))
        main_window.editor.load_page(folder_id)

        received = []
        main_window.editor.navigate_to_page.connect(lambda pid: received.append(pid))
        buttons = main_window.editor._toc_widget.findChildren(
            __import__("PyQt6.QtWidgets", fromlist=["QPushButton"]).QPushButton
        )
        assert len(buttons) == 1
        buttons[0].click()
        assert received == [child_id]

    def test_regular_page_no_toc(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        assert main_window.editor._toc_widget is None

    def test_page_title_set_for_folder(self, main_window):
        folder_id = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        main_window.editor.load_page(folder_id)
        assert main_window.editor.page_title.text() == "MyFolder"

    def test_toc_multiple_children(self, main_window):
        folder_id = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        PageRepo().create(Page(title="A", parent_id=folder_id))
        PageRepo().create(Page(title="B", parent_id=folder_id))
        PageRepo().create(Page(title="C", parent_id=folder_id))
        main_window.editor.load_page(folder_id)
        buttons = main_window.editor._toc_widget.findChildren(
            __import__("PyQt6.QtWidgets", fromlist=["QPushButton"]).QPushButton
        )
        assert len(buttons) == 3


class TestBackToFolderButton:
    def test_back_button_hidden_initially(self, main_window):
        assert not main_window.editor._back_btn.isVisible()

    def test_back_button_shown_for_child_page(self, main_window):
        folder_id = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        child_id = PageRepo().create(Page(title="Child", parent_id=folder_id))
        main_window.editor.load_page(child_id)
        assert main_window.editor._back_btn.isVisible()

    def test_back_button_hidden_for_root_page(self, main_window):
        pid = PageRepo().create(Page(title="RootPage"))
        main_window.editor.load_page(pid)
        assert not main_window.editor._back_btn.isVisible()

    def test_back_button_hidden_for_folder(self, main_window):
        folder_id = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        main_window.editor.load_page(folder_id)
        assert not main_window.editor._back_btn.isVisible()

    def test_back_button_hidden_on_clear(self, main_window):
        folder_id = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        child_id = PageRepo().create(Page(title="Child", parent_id=folder_id))
        main_window.editor.load_page(child_id)
        main_window.editor.clear_editor()
        assert not main_window.editor._back_btn.isVisible()

    def test_back_button_emits_signal(self, main_window):
        folder_id = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        child_id = PageRepo().create(Page(title="Child", parent_id=folder_id))
        main_window.editor.load_page(child_id)
        received = []
        main_window.editor.navigate_to_page.connect(lambda pid: received.append(pid))
        main_window.editor._back_btn.click()
        assert received == [folder_id]

    def test_back_button_text(self, main_window):
        folder_id = PageRepo().create(Page(title="MyFolder", page_type="folder"))
        child_id = PageRepo().create(Page(title="Child", parent_id=folder_id))
        main_window.editor.load_page(child_id)
        assert "Back to folder" in main_window.editor._back_btn.text()


class TestTemplateButton:
    def test_template_button_exists(self, main_window):
        assert main_window.sidebar.btn_template is not None

    def test_template_button_text(self, main_window):
        assert "Set as Template" in main_window.sidebar.btn_template.text()

    def test_template_button_with_page_loaded(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        assert main_window.sidebar._editor_ref.current_page_id == pid


class TestCheckboxFeature:
    def test_checkbox_btn_hidden_initially(self, main_window):
        assert not main_window.editor._checkbox_btn.isVisible()

    def test_checkbox_btn_shown_on_page_load(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        assert main_window.editor._checkbox_btn.isVisible()

    def test_checkbox_btn_hidden_for_folder(self, main_window):
        fid = PageRepo().create(Page(title="Folder", page_type="folder"))
        main_window.editor.load_page(fid)
        assert not main_window.editor._checkbox_btn.isVisible()

    def test_add_checklist_creates_widget(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()
        assert len(main_window.editor._checklists) == 1

    def test_add_checklist_hides_empty_hint(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        assert main_window.editor._page_empty_hint.isVisible()
        main_window.editor._add_checklist()
        assert not main_window.editor._page_empty_hint.isVisible()

    def test_checkbox_persists_in_db(self, main_window):
        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()
        objects = PageObjectRepo().get_by_page(pid)
        assert len(objects) == 1
        assert objects[0].object_type == "checkbox"

    def test_checkbox_loads_on_page_reload(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()
        main_window.editor.clear_editor()
        main_window.editor.load_page(pid)
        assert len(main_window.editor._objects) == 1

    def test_checkbox_state_persists(self, main_window):
        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()
        widget = list(main_window.editor._checklists.values())[0]
        item = widget._checkboxes_layout.itemAt(0).widget()
        item._checkbox.setChecked(True)
        objects = PageObjectRepo().get_by_page(pid)
        assert objects[0].is_checked

    def test_floating_add_button_exists(self, main_window):
        assert main_window.editor._add_btn is not None

    def test_multiple_checklists(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()
        main_window.editor._add_checklist()
        assert len(main_window.editor._checklists) == 2

    def test_add_item_to_checklist(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()
        checklist = list(main_window.editor._checklists.values())[0]
        checklist._add_item()
        assert checklist._checkboxes_layout.count() == 2

    def test_add_item_text_is_string(self, main_window):
        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()
        checklist = list(main_window.editor._checklists.values())[0]
        checklist._add_item(text="Test task")
        obj = PageObjectRepo().get_by_page(pid)[0]
        content = json.loads(obj.content)
        assert isinstance(content["text"], str)

    def test_load_objects_handles_bool_text(self, main_window):
        from src.models.page_object import PageObject
        from src.repositories.page_object_repo import PageObjectRepo
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        obj = PageObject(
            page_id=pid,
            object_type="checkbox",
            content=json.dumps({"text": True, "checked": False}),
        )
        obj.id = PageObjectRepo().create(obj)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.load_objects([obj])

        assert checklist._checkboxes_layout.count() == 1
        item = checklist._checkboxes_layout.itemAt(0).widget()
        assert item._text_edit.text() == "True"
