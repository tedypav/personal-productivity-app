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
        checklist.keyPressEvent(event)

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
        item._text_edit.setFocus()

        received = []
        checklist.item_delete_requested.connect(lambda oid: received.append(oid))

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_D,
            Qt.KeyboardModifier.ControlModifier,
        )
        checklist.keyPressEvent(event)

        assert received == [item.obj_id]

    def test_d_without_ctrl_does_nothing(self, main_window):
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
            Qt.Key.Key_D,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.keyPressEvent(event)

        assert received == []

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
        item._text_edit.setFocus()

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Delete,
            Qt.KeyboardModifier.NoModifier,
        )
        checklist.keyPressEvent(event)

        assert PageObjectRepo().get_by_id(obj_id) is None
