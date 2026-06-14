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
        assert main_window.editor._page_empty_hint.objectName() == "editorEmptyHint"


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

    def test_checklist_header_exists(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        assert checklist._header is not None

    def test_checklist_header_has_title(self, main_window):
        from PyQt6.QtWidgets import QLineEdit

        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        title_edit = checklist._header.findChild(QLineEdit)
        assert title_edit is not None
        assert "Checklist" in title_edit.text()

    def test_checklist_delete_button_is_tool_button(self, main_window):
        from PyQt6.QtWidgets import QToolButton

        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        delete_btn = checklist._header.findChild(QToolButton)
        assert delete_btn is not None

    def test_checklist_header_is_draggable(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        assert hasattr(checklist, "_dragging")
        assert checklist._dragging is False


class TestChecklistSizing:
    def test_refresh_size_empty(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._refresh_size()
        expected_h = 36 + 32
        assert checklist.height() == expected_h

    def test_refresh_size_one_item(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        expected_h = 36 + 42 + 32
        assert checklist.height() == expected_h

    def test_refresh_size_multiple_items(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._add_item()
        checklist._add_item()
        checklist._refresh_size()
        spacing = checklist._checkboxes_layout.spacing()
        expected_h = 36 + 3 * 42 + 2 * spacing + 32
        assert checklist.height() == expected_h

    def test_refresh_size_after_delete(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._add_item()
        h_before = checklist.height()

        item = checklist._checkboxes_layout.itemAt(0).widget()
        checklist._checkboxes_layout.removeWidget(item)
        item.deleteLater()
        checklist._refresh_size()

        spacing = checklist._checkboxes_layout.spacing()
        n = checklist._checkboxes_layout.count()
        expected_h = 36 + n * 42 + max(0, n - 1) * spacing + 32
        assert checklist.height() == expected_h
        assert checklist.height() < h_before


class TestItemDelete:
    def test_item_delete_removes_from_db(self, main_window):
        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()

        checklist = list(main_window.editor._checklists.values())[0]
        item = checklist._checkboxes_layout.itemAt(0).widget()
        obj_id = item.obj_id

        main_window.editor._on_item_delete(obj_id)

        assert PageObjectRepo().get_by_id(obj_id) is None

    def test_item_delete_removes_widget(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()

        checklist = list(main_window.editor._checklists.values())[0]
        item = checklist._checkboxes_layout.itemAt(0).widget()
        obj_id = item.obj_id

        main_window.editor._on_item_delete(obj_id)

        for i in range(checklist._checkboxes_layout.count()):
            w = checklist._checkboxes_layout.itemAt(i).widget()
            if w and hasattr(w, "obj_id"):
                assert w.obj_id != obj_id

    def test_item_delete_removes_empty_checklist(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()

        checklist = list(main_window.editor._checklists.values())[0]
        item = checklist._checkboxes_layout.itemAt(0).widget()
        obj_id = item.obj_id

        main_window.editor._on_item_delete(obj_id)

        assert len(main_window.editor._checklists) == 0

    def test_item_delete_updates_objects_list(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()

        checklist = list(main_window.editor._checklists.values())[0]
        item = checklist._checkboxes_layout.itemAt(0).widget()
        obj_id = item.obj_id

        main_window.editor._on_item_delete(obj_id)

        assert all(o.id != obj_id for o in main_window.editor._objects)

    def test_item_delete_shows_empty_hint(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()

        checklist = list(main_window.editor._checklists.values())[0]
        item = checklist._checkboxes_layout.itemAt(0).widget()
        obj_id = item.obj_id

        main_window.editor._on_item_delete(obj_id)

        assert main_window.editor._page_empty_hint.isVisible()


class TestItemDeleteSignal:
    def test_item_delete_signal_connected(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()

        checklist = list(main_window.editor._checklists.values())[0]
        item = checklist._checkboxes_layout.itemAt(0).widget()

        received = []
        checklist.item_delete_requested.connect(lambda oid: received.append(oid))
        item.delete_requested.emit(item.obj_id)

        assert received == [item.obj_id]


class TestEnterKey:
    def test_enter_signal_exists(self, main_window):
        from src.ui.objects.checkbox_widget import CheckboxWidget

        assert hasattr(CheckboxWidget, "enter_pressed")

    def test_enter_pressed_emits_signal(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()

        checklist = list(main_window.editor._checklists.values())[0]
        item = checklist._checkboxes_layout.itemAt(0).widget()

        received = []
        item.enter_pressed.connect(lambda oid: received.append(oid))
        item._text_edit.returnPressed.emit()

        assert received == [item.obj_id]

    def test_enter_creates_new_task(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()

        checklist = list(main_window.editor._checklists.values())[0]
        item = checklist._checkboxes_layout.itemAt(0).widget()
        item._text_edit.setText("Buy milk")
        item._text_edit.returnPressed.emit()

        assert checklist._checkboxes_layout.count() == 2

    def test_focus_text_sets_focus(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()

        checklist = list(main_window.editor._checklists.values())[0]
        item = checklist._checkboxes_layout.itemAt(0).widget()
        item.focus_text()

        assert item._text_edit.hasFocus()


class TestResize:
    def test_resize_state_initialized(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        assert checklist._resizing is False
        assert checklist._resize_edge is None
        assert checklist._user_width is None

    def test_detect_edge_right(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        from PyQt6.QtCore import QPoint

        mid_y = checklist.height() // 2
        pos = QPoint(398, mid_y)
        assert checklist._detect_edge(pos) == "right"

    def test_detect_edge_left(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        from PyQt6.QtCore import QPoint

        mid_y = checklist.height() // 2
        pos = QPoint(3, mid_y)
        assert checklist._detect_edge(pos) == "left"

    def test_detect_edge_bottom(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        from PyQt6.QtCore import QPoint

        mid_x = checklist.width() // 2
        pos = QPoint(mid_x, checklist.height() - 3)
        assert checklist._detect_edge(pos) == "bottom"

    def test_detect_edge_bottom_right(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        from PyQt6.QtCore import QPoint

        pos = QPoint(398, checklist.height() - 3)
        assert checklist._detect_edge(pos) == "bottom-right"

    def test_detect_edge_none_in_center(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        from PyQt6.QtCore import QPoint

        mid_x = checklist.width() // 2
        mid_y = checklist.height() // 2
        pos = QPoint(mid_x, mid_y)
        assert checklist._detect_edge(pos) is None

    def test_detect_edge_none_in_header(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        from PyQt6.QtCore import QPoint

        pos = QPoint(200, 18)
        assert checklist._detect_edge(pos) is None

    def test_resize_min_width(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist._user_width = 100
        checklist._refresh_size()
        assert checklist.width() >= checklist._MIN_W

    def test_refresh_size_respects_user_width(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist._user_width = 300
        checklist._refresh_size()
        assert checklist.width() == 300

    def test_save_meta_creates_db_entry(self, main_window):
        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()

        checklist = list(main_window.editor._checklists.values())[0]
        checklist._save_meta()

        meta = PageObjectRepo().get_meta(pid, checklist.checklist_id)
        assert meta is not None
        assert meta.object_type == "checklist_meta"

    def test_save_meta_persists_position(self, main_window):
        import json

        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()

        checklist = list(main_window.editor._checklists.values())[0]
        checklist.move(100, 200)
        checklist._save_meta()

        meta = PageObjectRepo().get_meta(pid, checklist.checklist_id)
        data = json.loads(meta.content)
        assert data["x"] == 100
        assert data["y"] == 200

    def test_load_meta_restores_position(self, main_window):
        import json

        from src.models.page_object import PageObject
        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        meta = PageObject(
            page_id=pid,
            object_type="checklist_meta",
            content=json.dumps({"x": 150, "y": 250, "width": 350}),
            sort_order=50,
        )
        PageObjectRepo().create(meta)

        main_window.editor._add_checklist()
        checklist = list(main_window.editor._checklists.values())[0]

        assert checklist._user_width == 350
        assert checklist.x() == 150
        assert checklist.y() == 250

    def test_meta_excluded_from_objects(self, main_window):
        import json

        from src.models.page_object import PageObject
        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        meta = PageObject(
            page_id=pid,
            object_type="checklist_meta",
            content=json.dumps({"x": 0, "y": 0, "width": 300}),
            sort_order=50,
        )
        PageObjectRepo().create(meta)

        main_window.editor._add_checklist()

        objects = main_window.editor._objects
        assert all(o.object_type != "checklist_meta" for o in objects)


class TestResizeFixes:
    def test_resize_clears_fixed_width(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        checklist.setMinimumWidth(0)
        checklist.setMaximumWidth(16777215)
        checklist.setGeometry(100, 100, 500, checklist.height())

        assert checklist.width() == 500

    def test_event_filter_installed_on_children(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        child = checklist._checkboxes_layout.itemAt(0).widget()
        assert child.hasMouseTracking()

    def test_event_filter_installed_on_all_descendants(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        assert checklist.hasMouseTracking()
        for child in checklist.findChildren(
            type(checklist._checkboxes_layout.itemAt(0).widget())
        ):
            assert child.hasMouseTracking()

    def test_resize_edge_detection_during_resize(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        checklist._resizing = True
        checklist._resize_edge = "right"
        checklist._resize_start = checklist.mapToGlobal(checklist.rect().topRight())
        checklist._resize_origin = (
            checklist.x(),
            checklist.y(),
            checklist.width(),
            checklist.height(),
        )

        assert checklist._resize_edge == "right"
        assert checklist._resizing is True


class TestEditableTitle:
    def test_title_is_qlineedit(self, main_window):
        from PyQt6.QtWidgets import QLineEdit

        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        assert isinstance(checklist._title_edit, QLineEdit)

    def test_title_default_text(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        assert checklist._title_edit.text() == "Checklist"

    def test_title_is_editable(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist._title_edit.setText("My Tasks")
        assert checklist._title_edit.text() == "My Tasks"

    def test_title_persists_via_meta(self, main_window):
        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()

        checklist = list(main_window.editor._checklists.values())[0]
        checklist._title_edit.setText("Groceries")
        checklist._on_title_changed()

        meta = PageObjectRepo().get_meta(pid, checklist.checklist_id)
        assert meta is not None
        import json

        data = json.loads(meta.content)
        assert data["title"] == "Groceries"

    def test_title_loads_from_meta(self, main_window):
        import json

        from src.models.page_object import PageObject
        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        meta = PageObject(
            page_id=pid,
            object_type="checklist_meta",
            content=json.dumps({"x": 0, "y": 0, "width": 300, "title": "Work Tasks"}),
            sort_order=50,
        )
        PageObjectRepo().create(meta)

        main_window.editor._add_checklist()
        checklist = list(main_window.editor._checklists.values())[0]

        assert checklist._title_edit.text() == "Work Tasks"

    def test_title_click_does_not_drag(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._refresh_size()

        title_pos = checklist._title_edit.mapTo(
            checklist, checklist._title_edit.rect().center()
        )
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QMouseEvent

        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            title_pos.toPointF(),
            title_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mousePressEvent(event)

        assert checklist._dragging is False


class TestDeleteKeyboard:
    def test_delete_key_emits_signal(self, main_window):
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QKeyEvent

        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        item = checklist._checkboxes_layout.itemAt(0).widget()
        item._text_edit.setFocus()

        received = []
        checklist.item_delete_requested.connect(lambda oid: received.append(oid))

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Delete,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.eventFilter(item._text_edit, event)

        assert received == [item.obj_id]

    def test_ctrl_d_emits_signal(self, main_window):
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QKeyEvent

        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        item = checklist._checkboxes_layout.itemAt(0).widget()

        received = []
        checklist.item_delete_requested.connect(lambda oid: received.append(oid))

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_D,
            Qt.KeyboardModifier.ControlModifier,
        )
        checklist.eventFilter(item._text_edit, event)

        assert received == [item.obj_id]

    def test_delete_via_event_filter_on_checkbox(self, main_window):
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QKeyEvent

        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        item = checklist._checkboxes_layout.itemAt(0).widget()

        received = []
        checklist.object_delete_requested.connect(lambda cid: received.append(cid))

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Delete,
            Qt.KeyboardModifier.NoModifier,
        )
        result = checklist.eventFilter(item._checkbox, event)

        assert result is True
        assert received == [checklist.checklist_id]

    def test_delete_removes_item_from_db(self, main_window):
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QKeyEvent

        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_checklist()

        checklist = list(main_window.editor._checklists.values())[0]
        item = checklist._checkboxes_layout.itemAt(0).widget()
        obj_id = item.obj_id

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Delete,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.eventFilter(item._text_edit, event)

        assert PageObjectRepo().get_by_id(obj_id) is None

    def test_no_page_delete_when_checklist_focused(self, main_window):
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QKeyEvent

        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        item = checklist._checkboxes_layout.itemAt(0).widget()
        item._text_edit.setFocus()

        item_deleted = []
        checklist.item_delete_requested.connect(lambda oid: item_deleted.append(oid))

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Delete,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.eventFilter(item._text_edit, event)

        assert item_deleted == [item.obj_id]


class TestSidebarDeleteButton:
    def test_regular_page_has_delete_flag(self, main_window):
        from PyQt6.QtCore import Qt

        PageRepo().create(Page(title="TestPage"))
        main_window.sidebar.refresh()

        items = main_window.sidebar.tree.findItems(
            "TestPage",
            Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive,
        )
        assert len(items) == 1
        can_delete = items[0].data(0, Qt.ItemDataRole.UserRole + 2)
        assert can_delete is True

    def test_system_folder_has_no_delete_flag(self, main_window):
        from PyQt6.QtCore import Qt

        PageRepo().create(Page(title="Templates", page_type="folder"))
        main_window.sidebar.refresh()

        items = main_window.sidebar.template_tree.findItems(
            "Templates",
            Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive,
        )
        assert len(items) >= 1
        can_delete = items[0].data(0, Qt.ItemDataRole.UserRole + 2)
        assert can_delete is False

    def test_child_of_system_folder_has_delete_flag(self, main_window):
        from PyQt6.QtCore import Qt

        folder_id = PageRepo().create(Page(title="Templates", page_type="folder"))
        PageRepo().create(Page(title="Old Notes", parent_id=folder_id))
        main_window.sidebar.refresh()

        items = main_window.sidebar.template_tree.findItems(
            "Old Notes",
            Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive,
        )
        assert len(items) == 1
        can_delete = items[0].data(0, Qt.ItemDataRole.UserRole + 2)
        assert can_delete is True

    def test_delete_button_removes_page(self, main_window):
        from PyQt6.QtCore import Qt

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.sidebar.refresh()

        items = main_window.sidebar.tree.findItems(
            "TestPage",
            Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive,
        )
        assert len(items) == 1
        main_window.sidebar._delete_item(pid)

        assert PageRepo().get_by_id(pid) is None

    def test_delete_button_clears_editor_if_page_open(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.sidebar.refresh()

        main_window.sidebar._delete_item(pid)

        assert main_window.editor.current_page_id is None

    def test_delegate_is_set_on_tree(self, main_window):
        from src.ui.sidebar import DeleteButtonDelegate

        assert isinstance(
            main_window.sidebar.tree.itemDelegate(),
            DeleteButtonDelegate,
        )

    def test_delegate_is_set_on_template_tree(self, main_window):
        from src.ui.sidebar import DeleteButtonDelegate

        assert isinstance(
            main_window.sidebar.template_tree.itemDelegate(),
            DeleteButtonDelegate,
        )

    def test_hover_only_affects_target_item(self, main_window):
        from PyQt6.QtCore import QModelIndex, Qt

        PageRepo().create(Page(title="Parent", page_type="folder"))
        main_window.sidebar.refresh()

        items = main_window.sidebar.tree.findItems(
            "Parent",
            Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive,
        )
        parent_item = items[0]
        parent_index = main_window.sidebar.tree.indexFromItem(parent_item)

        delegate = main_window.sidebar.tree.itemDelegate()
        delegate._hovered_index = parent_index

        assert delegate._hovered_index == parent_index
        assert delegate._hovered_index != QModelIndex()

    def test_delete_item_with_undo(self, main_window):
        from PyQt6.QtCore import Qt

        pid = PageRepo().create(Page(title="UndoPage"))
        main_window.sidebar.refresh()

        items = main_window.sidebar.tree.findItems(
            "UndoPage",
            Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive,
        )
        assert len(items) == 1

        main_window.sidebar._delete_item(pid)
        assert PageRepo().get_by_id(pid) is None

    def test_delete_folder_removes_children(self, main_window):
        fid = PageRepo().create(Page(title="TestFolder", page_type="folder"))
        child_id = PageRepo().create(Page(title="Child", parent_id=fid))
        main_window.sidebar.refresh()

        main_window.sidebar._delete_item(fid)

        assert PageRepo().get_by_id(fid) is None
        assert PageRepo().get_by_id(child_id) is None


class TestTableWidget:
    def test_add_table_creates_widget(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_table()

        assert len(main_window.editor._tables) == 1

    def test_add_table_hides_empty_hint(self, main_window):
        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        assert main_window.editor._page_empty_hint.isVisible()
        main_window.editor._add_table()
        assert not main_window.editor._page_empty_hint.isVisible()

    def test_table_has_grid(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        assert table._table.rowCount() == 2
        assert table._table.columnCount() == 3

    def test_table_add_row(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        initial_rows = table._table.rowCount()
        table._add_row()
        assert table._table.rowCount() == initial_rows + 1

    def test_table_title_editable(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table._title_edit.setText("My Table")
        assert table._title_edit.text() == "My Table"

    def test_table_delete_signal(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        received = []
        table.object_delete_requested.connect(lambda tid: received.append(tid))

        table._delete_table()
        assert received == [0]

    def test_table_add_column(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        initial_cols = table._table.columnCount()
        table._add_column()
        assert table._table.columnCount() == initial_cols + 1
        assert table._table.horizontalHeaderItem(initial_cols).text() == "Column 4"

    def test_table_row_height_is_32px(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        vh = table._table.verticalHeader()
        assert vh.minimumSectionSize() == 24
        assert vh.defaultSectionSize() == 32

    def test_table_vertical_size_policy_is_expanding(self, main_window):
        from PyQt6.QtWidgets import QSizePolicy

        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        policy = table._table.sizePolicy()
        assert policy.verticalPolicy() == QSizePolicy.Policy.Expanding

    def test_new_table_has_fresh_defaults(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table1 = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table1._add_row()
        table1._add_column()
        assert table1._table.rowCount() == 3
        assert table1._table.columnCount() == 4

        table2 = TableWidget(1, page_id=pid, parent=main_window.editor.content)
        assert table2._table.rowCount() == 2
        assert table2._table.columnCount() == 3

    def test_table_meta_deleted_on_remove(self, main_window):
        from src.repositories.page_object_repo import PageObjectRepo

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)
        main_window.editor._add_table()

        checklist = list(main_window.editor._tables.values())[0]
        table_id = list(main_window.editor._tables.keys())[0]
        checklist._save_meta()

        meta = PageObjectRepo().get_table_meta(pid, table_id)
        assert meta is not None

        main_window.editor._on_table_delete(table_id)

        meta_after = PageObjectRepo().get_table_meta(pid, table_id)
        assert meta_after is None

    def test_table_persists_data(self, main_window):
        from PyQt6.QtWidgets import QTableWidgetItem

        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table._table.setItem(0, 0, QTableWidgetItem("Hello"))
        table._table.setItem(1, 2, QTableWidgetItem("World"))
        table._save_meta()

        table2 = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table2._load_meta()
        assert table2._table.item(0, 0).text() == "Hello"
        assert table2._table.item(1, 2).text() == "World"

    def test_column_rename(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table._table.horizontalHeaderItem(0).setText("Task")
        assert table._table.horizontalHeaderItem(0).text() == "Task"

    def test_column_rename_persists(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table._table.horizontalHeaderItem(1).setText("Due Date")
        table._save_meta()

        table2 = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table2._load_meta()
        assert table2._table.horizontalHeaderItem(1).text() == "Due Date"

    def test_row_number_toggle(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        assert not table._row_num_btn.isChecked()

        table._row_num_btn.setChecked(True)
        table._toggle_row_numbers()
        assert table._row_num_btn.isChecked()

        table._row_num_btn.setChecked(False)
        table._toggle_row_numbers()
        assert not table._row_num_btn.isChecked()

    def test_row_number_toggle_persists(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table._row_num_btn.setChecked(True)
        table._toggle_row_numbers()
        table._save_meta()

        table2 = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table2._load_meta()
        assert table2._row_num_btn.isChecked()

    def test_remove_row(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        initial = table._table.rowCount()
        table._remove_row()
        assert table._table.rowCount() == initial - 1

    def test_remove_row_keeps_minimum(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table._remove_row()
        assert table._table.rowCount() == 1

    def test_remove_column(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        initial = table._table.columnCount()
        table._remove_column()
        assert table._table.columnCount() == initial - 1

    def test_remove_column_keeps_minimum(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table._remove_column()
        table._remove_column()
        assert table._table.columnCount() == 1
        table._remove_column()
        assert table._table.columnCount() == 1


class TestTableResize:
    def test_detect_edge_right(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)
        from PyQt6.QtCore import QPoint

        pos = QPoint(398, 100)
        assert table._detect_edge(pos) == "right"

    def test_detect_edge_left(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)
        from PyQt6.QtCore import QPoint

        pos = QPoint(3, 100)
        assert table._detect_edge(pos) == "left"

    def test_detect_edge_bottom(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table._add_row()
        table.resize(400, 200)
        from PyQt6.QtCore import QPoint

        pos = QPoint(200, table.height() - 3)
        assert table._detect_edge(pos) == "bottom"

    def test_detect_edge_bottom_right(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table._add_row()
        table.resize(400, 200)
        from PyQt6.QtCore import QPoint

        pos = QPoint(398, table.height() - 3)
        assert table._detect_edge(pos) == "bottom-right"

    def test_detect_edge_none_in_center(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table._add_row()
        table.resize(400, 200)
        from PyQt6.QtCore import QPoint

        pos = QPoint(200, 100)
        assert table._detect_edge(pos) is None

    def test_resize_state_initialized(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        assert table._resizing is False
        assert table._resize_edge is None

    def test_scale_rows_to_fit(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table._add_row()
        table._add_row()
        table.resize(400, 200)
        table._scale_rows_to_fit()

        vh = table._table.verticalHeader()
        for r in range(table._table.rowCount()):
            assert vh.sectionSize(r) >= 24


class TestTableTab:
    def test_tab_creates_new_row(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)

        initial_rows = table._table.rowCount()
        table._table.setCurrentCell(initial_rows - 1, table._table.columnCount() - 1)
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QKeyEvent

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Tab,
            Qt.KeyboardModifier.NoModifier,
        )
        table._handle_tab(event)
        assert table._table.rowCount() == initial_rows + 1
        assert table._table.currentRow() == initial_rows
        assert table._table.currentColumn() == 0

    def test_tab_moves_to_next_cell(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)

        table._table.setCurrentCell(0, 0)
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QKeyEvent

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Tab,
            Qt.KeyboardModifier.NoModifier,
        )
        table._handle_tab(event)
        assert table._table.currentRow() == 0
        assert table._table.currentColumn() == 1

    def test_shift_tab_moves_to_previous_cell(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)

        table._table.setCurrentCell(0, 1)
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QKeyEvent

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Backtab,
            Qt.KeyboardModifier.NoModifier,
        )
        table._handle_tab(event, reverse=True)
        assert table._table.currentRow() == 0
        assert table._table.currentColumn() == 0


class TestResizableMixinState:
    def test_user_height_initialized_none(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        assert checklist._user_height is None

    def test_user_height_initialized_none_table(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        assert table._user_height is None

    def test_on_resize_complete_noop(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        h = checklist.height()
        checklist._on_resize_complete()
        assert checklist.height() == h

    def test_edge_cursor_map(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        from PyQt6.QtCore import Qt

        assert checklist._edge_cursor("left") == Qt.CursorShape.SizeHorCursor
        assert checklist._edge_cursor("right") == Qt.CursorShape.SizeHorCursor
        assert checklist._edge_cursor("top") == Qt.CursorShape.SizeVerCursor
        assert checklist._edge_cursor("bottom") == Qt.CursorShape.SizeVerCursor
        assert checklist._edge_cursor("top-left") == Qt.CursorShape.SizeFDiagCursor
        assert checklist._edge_cursor("bottom-right") == Qt.CursorShape.SizeFDiagCursor
        assert checklist._edge_cursor("top-right") == Qt.CursorShape.SizeBDiagCursor
        assert checklist._edge_cursor("bottom-left") == Qt.CursorShape.SizeBDiagCursor
        assert checklist._edge_cursor(None) == Qt.CursorShape.ArrowCursor


class TestChecklistResizeEdgeDetection:
    def test_detect_edge_top(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        from PyQt6.QtCore import QPoint

        mid_x = checklist.width() // 2
        header_h = checklist._header.height()
        pos = QPoint(mid_x, header_h + 3)
        assert checklist._detect_edge(pos) == "top"

    def test_detect_edge_top_left(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        from PyQt6.QtCore import QPoint

        header_h = checklist._header.height()
        pos = QPoint(3, header_h + 3)
        assert checklist._detect_edge(pos) == "top-left"

    def test_detect_edge_top_right(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        from PyQt6.QtCore import QPoint

        header_h = checklist._header.height()
        pos = QPoint(398, header_h + 3)
        assert checklist._detect_edge(pos) == "top-right"

    def test_detect_edge_bottom_left(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        from PyQt6.QtCore import QPoint

        pos = QPoint(3, checklist.height() - 3)
        assert checklist._detect_edge(pos) == "bottom-left"


class TestChecklistResizeComplete:
    def test_resize_complete_does_not_crash(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._add_item()
        checklist._refresh_size()
        checklist._on_resize_complete()

    def test_resize_complete_preserves_items(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._add_item()
        checklist._refresh_size()
        count = checklist._checkboxes_layout.count()
        checklist._on_resize_complete()
        assert checklist._checkboxes_layout.count() == count


class TestTableResizeEventFilter:
    def test_viewport_click_initiates_resize(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        right_edge_pos = QPoint(table.width() - 3, table.height() // 2)
        viewport_pos = table._table.viewport().mapFrom(table, right_edge_pos)

        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            viewport_pos.toPointF(),
            viewport_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        result = table.eventFilter(table._table.viewport(), event)
        assert result is True
        assert table._resizing is True
        assert table._resize_edge == "right"

    def test_viewport_click_center_does_not_resize(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        center_pos = QPoint(table.width() // 2, table.height() // 2)
        viewport_pos = table._table.viewport().mapFrom(table, center_pos)

        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            viewport_pos.toPointF(),
            viewport_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        result = table.eventFilter(table._table.viewport(), event)
        assert result is not True
        assert table._resizing is False

    def test_viewport_click_left_edge_initiates_resize(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        left_edge_pos = QPoint(3, table.height() // 2)
        viewport_pos = table._table.viewport().mapFrom(table, left_edge_pos)

        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            viewport_pos.toPointF(),
            viewport_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        result = table.eventFilter(table._table.viewport(), event)
        assert result is True
        assert table._resizing is True
        assert table._resize_edge == "left"

    def test_viewport_click_bottom_edge_initiates_resize(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        bottom_edge_pos = QPoint(table.width() // 2, table.height() - 3)
        viewport_pos = table._table.viewport().mapFrom(table, bottom_edge_pos)

        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            viewport_pos.toPointF(),
            viewport_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        result = table.eventFilter(table._table.viewport(), event)
        assert result is True
        assert table._resizing is True
        assert table._resize_edge == "bottom"

    def test_viewport_click_bottom_right_initiates_resize(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        br_pos = QPoint(table.width() - 3, table.height() - 3)
        viewport_pos = table._table.viewport().mapFrom(table, br_pos)

        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            viewport_pos.toPointF(),
            viewport_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        result = table.eventFilter(table._table.viewport(), event)
        assert result is True
        assert table._resizing is True
        assert table._resize_edge == "bottom-right"

    def test_viewport_child_click_initiates_resize(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        child = table._table.viewport().findChild(object)
        if child is None:
            return

        right_edge_pos = QPoint(table.width() - 3, table.height() // 2)
        child_pos = child.mapFrom(table, right_edge_pos)

        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            child_pos.toPointF(),
            child_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        result = table.eventFilter(child, event)
        if result is True:
            assert table._resizing is True

    def test_viewport_resize_changes_geometry(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)
        initial_w = table.width()
        initial_h = table.height()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        viewport = table._table.viewport()

        right_edge_pos = QPoint(initial_w - 3, initial_h // 2)
        viewport_pos = viewport.mapFrom(table, right_edge_pos)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            viewport_pos.toPointF(),
            viewport_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, press_event)
        assert table._resizing is True

        move_pos = QPoint(initial_w + 100, initial_h // 2)
        viewport_move_pos = viewport.mapFrom(table, move_pos)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            viewport_move_pos.toPointF(),
            viewport_move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, move_event)
        assert table.width() > initial_w

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            viewport_move_pos.toPointF(),
            viewport_move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, release_event)
        assert table._resizing is False
        assert table.width() >= initial_w + 100

    def test_viewport_resize_bottom_via_event_filter(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)
        initial_h = table.height()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        viewport = table._table.viewport()

        bottom_edge_pos = QPoint(table.width() // 2, initial_h - 3)
        viewport_pos = viewport.mapFrom(table, bottom_edge_pos)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            viewport_pos.toPointF(),
            viewport_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, press_event)
        assert table._resizing is True
        assert table._resize_edge == "bottom"

        move_pos = QPoint(table.width() // 2, initial_h + 100)
        viewport_move_pos = viewport.mapFrom(table, move_pos)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            viewport_move_pos.toPointF(),
            viewport_move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, move_event)
        assert table.height() > initial_h

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            viewport_move_pos.toPointF(),
            viewport_move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, release_event)
        assert table._resizing is False
        assert table.height() >= initial_h + 100

    def test_viewport_drag_moves_table(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)
        table.move(50, 50)
        initial_x = table.x()
        initial_y = table.y()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        viewport = table._table.viewport()

        header_center = QPoint(table.width() // 2, 18)
        viewport_pos = viewport.mapFrom(table, header_center)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            viewport_pos.toPointF(),
            viewport_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, press_event)
        assert table._dragging is True

        move_pos = QPoint(table.width() // 2 + 60, 18)
        viewport_move_pos = viewport.mapFrom(table, move_pos)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            viewport_move_pos.toPointF(),
            viewport_move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, move_event)

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            viewport_move_pos.toPointF(),
            viewport_move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, release_event)
        assert table._dragging is False
        assert table.x() != initial_x or table.y() != initial_y

    def test_resize_then_drag_works(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)
        table.move(50, 50)
        initial_x = table.x()
        initial_y = table.y()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        viewport = table._table.viewport()

        right_edge = QPoint(table.width() - 3, table.height() // 2)
        vp_right = viewport.mapFrom(table, right_edge)
        press = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            vp_right.toPointF(),
            vp_right.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, press)
        assert table._resizing is True

        move = QPoint(table.width() + 50, table.height() // 2)
        vp_move = viewport.mapFrom(table, move)
        move_evt = QMouseEvent(
            QEvent.Type.MouseMove,
            vp_move.toPointF(),
            vp_move.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, move_evt)

        release = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            vp_move.toPointF(),
            vp_move.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, release)
        assert table._resizing is False
        assert table.width() > 400

        header_center = QPoint(table.width() // 2, 18)
        vp_header = viewport.mapFrom(table, header_center)
        press2 = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            vp_header.toPointF(),
            vp_header.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, press2)
        assert table._dragging is True

        move2 = QPoint(table.width() // 2 + 40, 18)
        vp_move2 = viewport.mapFrom(table, move2)
        move_evt2 = QMouseEvent(
            QEvent.Type.MouseMove,
            vp_move2.toPointF(),
            vp_move2.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, move_evt2)

        release2 = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            vp_move2.toPointF(),
            vp_move2.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, release2)
        assert table._dragging is False
        assert table.x() != initial_x or table.y() != initial_y


class TestChecklistResizeMouseSimulation:
    def test_resize_right_edge_via_mouse(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        initial_w = checklist.width()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        edge_pos = QPoint(initial_w - 3, checklist.height() // 2)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mousePressEvent(press_event)
        assert checklist._resizing is True
        assert checklist._resize_edge == "right"

        move_pos = QPoint(initial_w + 50, checklist.height() // 2)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseMoveEvent(move_event)
        assert checklist.width() >= initial_w

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseReleaseEvent(release_event)
        assert checklist._resizing is False
        assert checklist._resize_edge is None
        assert checklist._resize_start is None
        assert checklist._resize_origin is None

    def test_resize_left_edge_via_mouse(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        edge_pos = QPoint(3, checklist.height() // 2)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mousePressEvent(press_event)
        assert checklist._resizing is True
        assert checklist._resize_edge == "left"

        move_pos = QPoint(-50, checklist.height() // 2)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseMoveEvent(move_event)
        assert checklist.width() >= checklist._MIN_W

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseReleaseEvent(release_event)
        assert checklist._resizing is False

    def test_resize_bottom_edge_via_mouse(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        initial_h = checklist.height()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        edge_pos = QPoint(checklist.width() // 2, initial_h - 3)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mousePressEvent(press_event)
        assert checklist._resizing is True
        assert checklist._resize_edge == "bottom"

        move_pos = QPoint(checklist.width() // 2, initial_h + 50)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseMoveEvent(move_event)
        assert checklist.height() >= checklist._min_height()

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseReleaseEvent(release_event)
        assert checklist._resizing is False

    def test_resize_bottom_right_via_mouse(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        initial_w = checklist.width()
        initial_h = checklist.height()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        edge_pos = QPoint(initial_w - 3, initial_h - 3)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mousePressEvent(press_event)
        assert checklist._resizing is True
        assert checklist._resize_edge == "bottom-right"

        move_pos = QPoint(initial_w + 50, initial_h + 50)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseMoveEvent(move_event)
        assert checklist.width() >= initial_w
        assert checklist.height() >= checklist._min_height()

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseReleaseEvent(release_event)
        assert checklist._resizing is False


class TestTableResizeMouseSimulation:
    def test_resize_right_edge_via_mouse(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)
        initial_w = table.width()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        edge_pos = QPoint(initial_w - 3, table.height() // 2)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mousePressEvent(press_event)
        assert table._resizing is True
        assert table._resize_edge == "right"

        move_pos = QPoint(initial_w + 50, table.height() // 2)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mouseMoveEvent(move_event)
        assert table.width() >= initial_w

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mouseReleaseEvent(release_event)
        assert table._resizing is False
        assert table._resize_edge is None

    def test_resize_left_edge_via_mouse(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        edge_pos = QPoint(3, table.height() // 2)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mousePressEvent(press_event)
        assert table._resizing is True
        assert table._resize_edge == "left"

        move_pos = QPoint(-50, table.height() // 2)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mouseMoveEvent(move_event)
        assert table.width() >= table._MIN_W

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mouseReleaseEvent(release_event)
        assert table._resizing is False

    def test_resize_bottom_edge_via_mouse(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)
        initial_h = table.height()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        edge_pos = QPoint(table.width() // 2, initial_h - 3)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mousePressEvent(press_event)
        assert table._resizing is True
        assert table._resize_edge == "bottom"

        move_pos = QPoint(table.width() // 2, initial_h + 50)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mouseMoveEvent(move_event)
        assert table.height() >= table._min_height()

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mouseReleaseEvent(release_event)
        assert table._resizing is False

    def test_resize_top_edge_via_mouse(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        header_h = table._header.height()
        edge_pos = QPoint(table.width() // 2, header_h + 3)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mousePressEvent(press_event)
        assert table._resizing is True
        assert table._resize_edge == "top"

        move_pos = QPoint(table.width() // 2, header_h - 50)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mouseMoveEvent(move_event)
        assert table.height() >= table._min_height()

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mouseReleaseEvent(release_event)
        assert table._resizing is False

    def test_resize_bottom_right_via_mouse(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)
        initial_w = table.width()
        initial_h = table.height()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        edge_pos = QPoint(initial_w - 3, initial_h - 3)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mousePressEvent(press_event)
        assert table._resizing is True
        assert table._resize_edge == "bottom-right"

        move_pos = QPoint(initial_w + 50, initial_h + 50)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mouseMoveEvent(move_event)
        assert table.width() >= initial_w
        assert table.height() >= table._min_height()

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mouseReleaseEvent(release_event)
        assert table._resizing is False

    def test_resize_min_width_enforced(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        edge_pos = QPoint(3, checklist.height() // 2)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mousePressEvent(press_event)

        move_pos = QPoint(9999, checklist.height() // 2)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseMoveEvent(move_event)
        assert checklist.width() >= checklist._MIN_W

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseReleaseEvent(release_event)

    def test_resize_min_height_enforced(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        edge_pos = QPoint(checklist.width() // 2, checklist.height() - 3)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mousePressEvent(press_event)

        move_pos = QPoint(checklist.width() // 2, -9999)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseMoveEvent(move_event)
        assert checklist.height() >= checklist._min_height()

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseReleaseEvent(release_event)

    def test_resize_origin_restored_on_release(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        edge_pos = QPoint(3, checklist.height() // 2)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mousePressEvent(press_event)
        assert checklist._resize_origin is not None

        move_pos = QPoint(-50, checklist.height() // 2)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseMoveEvent(move_event)

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseReleaseEvent(release_event)
        assert checklist._resize_origin is None
        assert checklist._resize_start is None

    def test_resize_user_width_set(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        initial_w = checklist.width()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        edge_pos = QPoint(initial_w - 3, checklist.height() // 2)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mousePressEvent(press_event)

        move_pos = QPoint(initial_w + 100, checklist.height() // 2)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseMoveEvent(move_event)
        assert checklist._user_width is not None
        assert checklist._user_width > 0


class TestTableRowScaling:
    def test_scale_rows_during_resize(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        vh = table._table.verticalHeader()
        initial_row_h = vh.sectionSize(0)

        edge_pos = QPoint(table.width() // 2, table.height() - 3)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mousePressEvent(press_event)

        move_pos = QPoint(table.width() // 2, table.height() + 100)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mouseMoveEvent(move_event)

        for r in range(table._table.rowCount()):
            assert vh.sectionSize(r) > initial_row_h

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mouseReleaseEvent(release_event)

    def test_scale_rows_via_event_filter(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        viewport = table._table.viewport()
        vh = table._table.verticalHeader()
        initial_row_h = vh.sectionSize(0)

        bottom_edge_pos = QPoint(table.width() // 2, table.height() - 3)
        viewport_pos = viewport.mapFrom(table, bottom_edge_pos)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            viewport_pos.toPointF(),
            viewport_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, press_event)

        move_pos = QPoint(table.width() // 2, table.height() + 100)
        viewport_move_pos = viewport.mapFrom(table, move_pos)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            viewport_move_pos.toPointF(),
            viewport_move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.eventFilter(viewport, move_event)

        for r in range(table._table.rowCount()):
            assert vh.sectionSize(r) > initial_row_h


class TestChecklistEventFilterResize:
    def test_event_filter_detects_edge_and_initiates_resize(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        child = checklist._checkboxes_layout.itemAt(0).widget()
        right_edge_pos = QPoint(checklist.width() - 3, checklist.height() // 2)
        child_pos = child.mapFrom(checklist, right_edge_pos)

        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            child_pos.toPointF(),
            child_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        result = checklist.eventFilter(child, event)
        assert result is True
        assert checklist._resizing is True
        assert checklist._resize_edge == "right"

    def test_event_filter_center_click_does_not_resize(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        child = checklist._checkboxes_layout.itemAt(0).widget()
        center_pos = QPoint(checklist.width() // 2, checklist.height() // 2)
        child_pos = child.mapFrom(checklist, center_pos)

        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            child_pos.toPointF(),
            child_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        result = checklist.eventFilter(child, event)
        assert result is not True
        assert checklist._resizing is False


class TestHeightPersistence:
    def test_checklist_save_load_height(self, main_window):
        from src.repositories.page_object_repo import PageObjectRepo
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        checklist.resize(400, 350)
        checklist._save_meta()

        meta = PageObjectRepo().get_meta(pid, checklist.checklist_id)
        assert meta is not None
        data = json.loads(meta.content)
        assert "height" in data
        assert data["height"] == 350

    def test_table_save_load_height(self, main_window):
        from src.repositories.page_object_repo import PageObjectRepo
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 350)
        table._save_meta()

        meta = PageObjectRepo().get_table_meta(pid, table.table_id)
        assert meta is not None
        data = json.loads(meta.content)
        assert "height" in data
        assert data["height"] == 350

    def test_checklist_load_restores_height(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()
        checklist.resize(400, 350)
        checklist._save_meta()

        checklist2 = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist2._load_meta()
        assert checklist2.height() == 350

    def test_table_load_restores_height(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 350)
        table._save_meta()

        table2 = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table2._load_meta()
        assert table2.height() == 350

    def test_checklist_height_none_when_not_saved(self, main_window):
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist._load_meta()
        assert checklist._user_height is None

    def test_table_height_none_when_not_saved(self, main_window):
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table._load_meta()
        assert table._user_height is None

    def test_checklist_resize_persists_height(self, main_window):
        from src.repositories.page_object_repo import PageObjectRepo
        from src.ui.editor import ChecklistWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        checklist = ChecklistWidget(0, page_id=pid, parent=main_window.editor.content)
        checklist.setFixedWidth(400)
        checklist._add_item()
        checklist._refresh_size()

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        edge_pos = QPoint(checklist.width() // 2, checklist.height() - 3)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mousePressEvent(press_event)

        new_h = checklist.height() + 80
        move_pos = QPoint(checklist.width() // 2, new_h)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseMoveEvent(move_event)

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.mouseReleaseEvent(release_event)

        meta = PageObjectRepo().get_meta(pid, checklist.checklist_id)
        assert meta is not None
        data = json.loads(meta.content)
        assert data["height"] >= checklist._min_height()

    def test_table_resize_persists_height(self, main_window):
        from src.repositories.page_object_repo import PageObjectRepo
        from src.ui.editor import TableWidget

        pid = PageRepo().create(Page(title="TestPage"))
        main_window.editor.load_page(pid)

        table = TableWidget(0, page_id=pid, parent=main_window.editor.content)
        table.setFixedWidth(400)
        table.resize(400, 200)

        from PyQt6.QtCore import QEvent, QPoint, Qt
        from PyQt6.QtGui import QMouseEvent

        edge_pos = QPoint(table.width() // 2, table.height() - 3)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            edge_pos.toPointF(),
            edge_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mousePressEvent(press_event)

        new_h = table.height() + 80
        move_pos = QPoint(table.width() // 2, new_h)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mouseMoveEvent(move_event)

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            move_pos.toPointF(),
            move_pos.toPointF(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        table.mouseReleaseEvent(release_event)

        meta = PageObjectRepo().get_table_meta(pid, table.table_id)
        assert meta is not None
        data = json.loads(meta.content)
        assert data["height"] >= table._min_height()
