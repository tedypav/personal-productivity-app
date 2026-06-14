import os
import tempfile

from PyQt6.QtWidgets import QTextEdit

from src.ui.fun_imports import FunImportsDialog


class TestFunImportsInsertGif:
    def test_insert_gif_adds_html_img(self, app_instance):
        edit = QTextEdit()
        dialog = FunImportsDialog(target_edit=edit)
        gif_path = os.path.join(tempfile.gettempdir(), "test.gif")
        with open(gif_path, "wb") as f:
            f.write(b"GIF89a")
        dialog._insert_gif(gif_path)
        html = edit.toHtml()
        assert "<img" in html
        assert "GIF89a" not in html
        os.unlink(gif_path)

    def test_insert_gif_does_not_insert_plain_text(self, app_instance):
        edit = QTextEdit()
        dialog = FunImportsDialog(target_edit=edit)
        gif_path = os.path.join(tempfile.gettempdir(), "test.gif")
        with open(gif_path, "wb") as f:
            f.write(b"GIF89a")
        dialog._insert_gif(gif_path)
        text = edit.toPlainText()
        assert "[GIF:" not in text
        os.unlink(gif_path)

    def test_insert_gif_no_target_edit(self, app_instance):
        dialog = FunImportsDialog(target_edit=None)
        dialog._insert_gif("/some/path.gif")
        assert not dialog.isVisible()

    def test_insert_gif_converts_local_path_to_file_url(self, app_instance):
        edit = QTextEdit()
        dialog = FunImportsDialog(target_edit=edit)
        gif_path = os.path.join(tempfile.gettempdir(), "test.gif")
        with open(gif_path, "wb") as f:
            f.write(b"GIF89a")
        dialog._insert_gif(gif_path)
        html = edit.toHtml()
        assert "file:///" in html or "file:" in html
        os.unlink(gif_path)
