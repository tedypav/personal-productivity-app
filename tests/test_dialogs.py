from unittest.mock import patch

from PyQt6.QtWidgets import QHBoxLayout, QLabel

from src.ui.dialogs import _get_icon_path, create_dialog_header


class TestGetIconPath:
    def test_returns_string(self):
        result = _get_icon_path("logo_icon")
        assert isinstance(result, str)

    def test_ends_with_svg(self):
        result = _get_icon_path("logo_icon")
        assert result.endswith("logo_icon.svg")

    def test_contains_assets_icons(self):
        result = _get_icon_path("logo_icon")
        assert "assets" in result
        assert "icons" in result

    def test_different_name(self):
        result = _get_icon_path("page")
        assert result.endswith("page.svg")


class TestCreateDialogHeader:
    def test_returns_layout(self, app_instance):
        layout = create_dialog_header("Test Title")
        assert isinstance(layout, QHBoxLayout)

    def test_contains_title_label(self, app_instance):
        layout = create_dialog_header("My Header")
        labels = [
            layout.itemAt(i).widget()
            for i in range(layout.count())
            if layout.itemAt(i).widget()
            and isinstance(layout.itemAt(i).widget(), QLabel)
        ]
        title_texts = [lbl.text() for lbl in labels]
        assert "My Header" in title_texts

    def test_has_stretch(self, app_instance):
        layout = create_dialog_header("Title")
        last_item = layout.itemAt(layout.count() - 1)
        assert last_item is not None
        assert last_item.widget() is None

    def test_empty_title(self, app_instance):
        layout = create_dialog_header("")
        assert isinstance(layout, QHBoxLayout)

    def test_logo_when_file_exists(self, app_instance):
        with patch("src.ui.dialogs.os.path.exists", return_value=True):
            layout = create_dialog_header("Title")
            assert layout.count() >= 2

    def test_logo_when_file_missing(self, app_instance):
        with patch("src.ui.dialogs.os.path.exists", return_value=False):
            layout = create_dialog_header("Title")
            labels = [
                layout.itemAt(i).widget()
                for i in range(layout.count())
                if layout.itemAt(i).widget()
                and isinstance(layout.itemAt(i).widget(), QLabel)
            ]
            assert len(labels) == 1
