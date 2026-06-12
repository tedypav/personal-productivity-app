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
            assert sizes[0] == 350
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
