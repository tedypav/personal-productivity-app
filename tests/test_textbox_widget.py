from src.controllers.textbox_controller import TextboxController
from src.models.page import Page
from src.models.page_object import PageObject
from src.repositories.page_object_repo import PageObjectRepo
from src.repositories.page_repo import PageRepo
from src.ui.objects.textbox_widget import (
    TextboxChecklistBlock,
    TextboxChecklistItem,
    TextboxImageBlock,
    TextboxTableBlock,
    TextboxTextBlock,
    TextboxWidget,
)


class TestTextboxController:
    def test_save_meta_creates_new(self, app_instance):
        pid = PageRepo().create(Page(title="Test"))
        ctrl = TextboxController()
        ctrl.save_meta(
            page_id=pid,
            textbox_id=0,
            x=10,
            y=20,
            width=400,
            height=300,
            title="My Box",
            blocks=[{"type": "text", "content": "<p>hi</p>"}],
        )
        meta = PageObjectRepo().get_textbox_meta(pid, 0)
        assert meta is not None
        assert meta.object_type == "textbox_meta"
        assert meta.sort_order == 50

    def test_save_meta_updates_existing(self, app_instance):
        pid = PageRepo().create(Page(title="Test"))
        ctrl = TextboxController()
        ctrl.save_meta(pid, 0, 10, 20, 400, 300, "v1", [])
        ctrl.save_meta(pid, 0, 10, 20, 400, 300, "v2", [])
        metas = [
            o
            for o in PageObjectRepo().get_by_page(pid)
            if o.object_type == "textbox_meta"
        ]
        assert len(metas) == 1

    def test_load_meta_returns_data(self, app_instance):
        pid = PageRepo().create(Page(title="Test"))
        ctrl = TextboxController()
        ctrl.save_meta(pid, 1, 0, 0, 500, 400, "Box", [])
        data = ctrl.load_meta(pid, 1)
        assert data is not None
        assert data["title"] == "Box"
        assert data["width"] == 500

    def test_load_meta_returns_none(self, app_instance):
        pid = PageRepo().create(Page(title="Test"))
        ctrl = TextboxController()
        assert ctrl.load_meta(pid, 999) is None


class TestTextboxTextBlock:
    def test_renders_html(self, app_instance):
        block = TextboxTextBlock(html="<p>Hello</p>")
        assert "Hello" in block._editor.toPlainText()

    def test_shows_placeholder_when_empty(self, app_instance):
        block = TextboxTextBlock()
        text = block._editor.toPlainText()
        assert "Double-click" in text or "start typing" in text

    def test_enter_edit_mode(self, app_instance):
        block = TextboxTextBlock(html="<p>Test</p>")
        block.show()
        block._enter_edit_mode()
        assert block._editing is True
        assert not block._editor.isReadOnly()

    def test_exit_edit_mode(self, app_instance):
        block = TextboxTextBlock(html="<p>Test</p>")
        block.show()
        block._enter_edit_mode()
        block.exit_edit_mode()
        assert block._editing is False
        assert block._editor.isReadOnly()

    def test_get_content_returns_html(self, app_instance):
        block = TextboxTextBlock(html="<p>Hi</p>")
        assert block.get_content() == "<p>Hi</p>"

    def test_set_content_updates_editor(self, app_instance):
        block = TextboxTextBlock()
        block.set_content("<p>New</p>")
        assert "New" in block._editor.toPlainText()

    def test_content_changed_signal(self, app_instance, qtbot):
        block = TextboxTextBlock()
        with qtbot.waitSignal(block.content_changed, raising=False):
            block.set_content("<p>Changed</p>")


class TestTextboxChecklistItem:
    def test_initially_unchecked(self, app_instance):
        item = TextboxChecklistItem()
        assert item._checked is False

    def test_checked_state(self, app_instance):
        item = TextboxChecklistItem(text="Task", checked=True)
        assert item._checked is True
        assert item._text.text() == "Task"

    def test_get_data(self, app_instance):
        item = TextboxChecklistItem(text="Buy milk", checked=True)
        data = item.get_data()
        assert data == {"text": "Buy milk", "checked": True}

    def test_set_data(self, app_instance):
        item = TextboxChecklistItem()
        item.set_data({"text": "Eggs", "checked": True})
        assert item._text.text() == "Eggs"
        assert item._checked is True


class TestTextboxChecklistBlock:
    def test_starts_empty(self, app_instance):
        block = TextboxChecklistBlock()
        assert block.get_content() == []

    def test_adds_default_item(self, app_instance):
        block = TextboxChecklistBlock(items=[{"text": "A", "checked": False}])
        data = block.get_content()
        assert len(data) == 1
        assert data[0]["text"] == "A"

    def test_add_item(self, app_instance):
        block = TextboxChecklistBlock()
        block._add_item(text="Task 1")
        assert len(block.get_content()) == 1

    def test_remove_item(self, app_instance):
        block = TextboxChecklistBlock(items=[{"text": "A", "checked": False}])
        item = block._items_layout.itemAt(0).widget()
        block._remove_item(item)
        assert len(block.get_content()) == 0


class TestTextboxTableBlock:
    def test_default_2x3(self, app_instance):
        block = TextboxTableBlock()
        assert block._table.rowCount() == 2
        assert block._table.columnCount() == 3

    def test_add_row(self, app_instance):
        block = TextboxTableBlock()
        block._add_row()
        assert block._table.rowCount() == 3

    def test_remove_row(self, app_instance):
        block = TextboxTableBlock()
        block._remove_row()
        assert block._table.rowCount() == 1

    def test_remove_row_minimum(self, app_instance):
        block = TextboxTableBlock()
        block._remove_row()
        block._remove_row()
        assert block._table.rowCount() == 1

    def test_add_col(self, app_instance):
        block = TextboxTableBlock()
        block._add_col()
        assert block._table.columnCount() == 4

    def test_remove_col(self, app_instance):
        block = TextboxTableBlock()
        block._remove_col()
        assert block._table.columnCount() == 2

    def test_remove_col_minimum(self, app_instance):
        block = TextboxTableBlock()
        block._remove_col()
        block._remove_col()
        assert block._table.columnCount() == 1

    def test_get_content(self, app_instance):
        block = TextboxTableBlock()
        data = block.get_content()
        assert "headers" in data
        assert "data" in data
        assert len(data["headers"]) == 3

    def test_set_content(self, app_instance):
        block = TextboxTableBlock()
        new_data = {
            "headers": ["A", "B"],
            "data": [["1", "2"], ["3", "4"]],
        }
        block.set_content(new_data)
        assert block._table.columnCount() == 2
        assert block._table.rowCount() == 2


class TestTextboxWidget:
    def test_creates_with_defaults(self, app_instance):
        pid = PageRepo().create(Page(title="Test"))
        w = TextboxWidget(textbox_id=1, page_id=pid)
        assert w.textbox_id == 1
        assert w.page_id == pid

    def test_has_header(self, app_instance):
        pid = PageRepo().create(Page(title="Test"))
        w = TextboxWidget(textbox_id=1, page_id=pid)
        assert w._header is not None
        assert w._title_edit.text() == "Text Box"

    def test_add_text_block(self, app_instance):
        pid = PageRepo().create(Page(title="Test"))
        w = TextboxWidget(textbox_id=1, page_id=pid)
        block = w._add_text_block(html="<p>Hi</p>")
        assert isinstance(block, TextboxTextBlock)
        assert len(w._blocks) == 1
        assert w._blocks[0][0] == "text"

    def test_add_checklist_block(self, app_instance):
        pid = PageRepo().create(Page(title="Test"))
        w = TextboxWidget(textbox_id=1, page_id=pid)
        block = w._add_checklist_block(items=[{"text": "A", "checked": False}])
        assert isinstance(block, TextboxChecklistBlock)
        assert len(w._blocks) == 1
        assert w._blocks[0][0] == "checklist"

    def test_add_table_block(self, app_instance):
        pid = PageRepo().create(Page(title="Test"))
        w = TextboxWidget(textbox_id=1, page_id=pid)
        block = w._add_table_block()
        assert isinstance(block, TextboxTableBlock)
        assert len(w._blocks) == 1
        assert w._blocks[0][0] == "table"

    def test_add_image_block(self, app_instance):
        pid = PageRepo().create(Page(title="Test"))
        w = TextboxWidget(textbox_id=1, page_id=pid)
        block = w._add_image_block()
        assert isinstance(block, TextboxImageBlock)
        assert len(w._blocks) == 1
        assert w._blocks[0][0] == "image"

    def test_delete_emits_signal(self, app_instance, qtbot):
        pid = PageRepo().create(Page(title="Test"))
        w = TextboxWidget(textbox_id=5, page_id=pid)
        with qtbot.waitSignal(w.object_delete_requested, raising=False) as b:
            w._delete_textbox()
        assert b.signal_triggered is True
        assert b.args == [5]

    def test_exit_all_edit_modes(self, app_instance):
        pid = PageRepo().create(Page(title="Test"))
        w = TextboxWidget(textbox_id=1, page_id=pid)
        block = w._add_text_block(html="<p>Hi</p>")
        block._enter_edit_mode()
        assert block._editing is True
        w.exit_all_edit_modes()
        assert block._editing is False

    def test_save_and_load_meta(self, app_instance):
        pid = PageRepo().create(Page(title="Test"))
        w = TextboxWidget(textbox_id=2, page_id=pid)
        w._add_text_block(html="<p>Hello</p>")
        w._add_checklist_block(items=[{"text": "Task", "checked": False}])
        w._title_edit.setText("My Box")
        w.move(50, 60)
        w.resize(450, 350)
        w._save_meta()

        w2 = TextboxWidget(textbox_id=2, page_id=pid)
        w2._load_meta()
        assert w2._title_edit.text() == "My Box"
        assert len(w2._blocks) == 2
        assert w2._blocks[0][0] == "text"
        assert w2._blocks[1][0] == "checklist"


class TestTextboxRepo:
    def test_get_textbox_meta(self, app_instance):
        pid = PageRepo().create(Page(title="Test"))
        obj = PageObject(
            page_id=pid,
            object_type="textbox_meta",
            content="{}",
            sort_order=150,
        )
        PageObjectRepo().create(obj)
        meta = PageObjectRepo().get_textbox_meta(pid, 1)
        assert meta is not None
        assert meta.sort_order == 150

    def test_get_textbox_meta_none(self, app_instance):
        pid = PageRepo().create(Page(title="Test"))
        assert PageObjectRepo().get_textbox_meta(pid, 999) is None
