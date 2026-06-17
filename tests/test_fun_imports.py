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


class TestFunImportsScrollToCategory:
    def test_scroll_to_known_category(self, app_instance):
        dialog = FunImportsDialog()
        dialog.show()

        dialog._scroll_to_category("Smileys")
        dialog.close()

    def test_scroll_to_unknown_category_does_not_crash(self, app_instance):
        dialog = FunImportsDialog()
        dialog.show()

        dialog._scroll_to_category("NonExistentCategory")
        dialog.close()


class TestFunImportsInsertEmoji:
    def test_insert_emoji_into_text_edit(self, app_instance):
        edit = QTextEdit()
        dialog = FunImportsDialog(target_edit=edit)
        dialog._insert_emoji("😀")
        text = edit.toPlainText()
        assert "😀" in text

    def test_insert_emoji_closes_dialog(self, app_instance):
        edit = QTextEdit()
        dialog = FunImportsDialog(target_edit=edit)
        dialog.show()
        dialog._insert_emoji("🔥")
        assert not dialog.isVisible()

    def test_insert_emoji_no_target_edit(self, app_instance):
        dialog = FunImportsDialog(target_edit=None)
        dialog._insert_emoji("🔥")
        assert not dialog.isVisible()

    def test_insert_emoji_with_plain_text_fallback(self, app_instance):
        class FakeEdit:
            def setFocus(self):
                pass

            def textCursor(self):
                raise Exception("no textCursor")

            def insertPlainText(self, text):
                self._text = getattr(self, "_text", "") + text

        edit = FakeEdit()
        dialog = FunImportsDialog(target_edit=edit)
        dialog._insert_emoji("❤️")
        assert "❤️" in edit._text


class TestFunImportsRebuildGifContent:
    def test_rebuild_clears_and_repopulates(self, app_instance):
        dialog = FunImportsDialog()
        dialog.show()

        initial_count = dialog._gif_layout.count()
        assert initial_count > 0

        dialog._rebuild_gif_content()

        new_count = dialog._gif_layout.count()
        assert new_count > 0
        dialog.close()
