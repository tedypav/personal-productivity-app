import json

from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QKeyEvent, QMouseEvent

from src.models.page import Page
from src.models.page_object import PageObject
from src.repositories.page_object_repo import PageObjectRepo
from src.repositories.page_repo import PageRepo
from src.ui.objects.checkbox_widget import CheckboxWidget, CustomCheckBox
from src.ui.objects.checklist_widget import ChecklistWidget


class TestCustomCheckBox:
    def test_initially_unchecked(self, app_instance):
        cb = CustomCheckBox()
        assert cb.isChecked() is False

    def test_initially_checked(self, app_instance):
        cb = CustomCheckBox(checked=True)
        assert cb.isChecked() is True

    def test_set_checked_true(self, app_instance):
        cb = CustomCheckBox()
        cb.setChecked(True)
        assert cb.isChecked() is True

    def test_set_checked_false(self, app_instance):
        cb = CustomCheckBox(checked=True)
        cb.setChecked(False)
        assert cb.isChecked() is False

    def test_set_checked_no_change_no_signal(self, app_instance):
        cb = CustomCheckBox(checked=True)
        emitted = []
        cb.stateChanged.connect(lambda v: emitted.append(v))
        cb.setChecked(True)
        assert emitted == []

    def test_set_checked_emits_signal(self, app_instance, qtbot):
        cb = CustomCheckBox()
        with qtbot.waitSignal(cb.stateChanged, raising=False) as blocker:
            cb.setChecked(True)
        assert blocker.signal_triggered is True

    def test_toggle(self, app_instance):
        cb = CustomCheckBox()
        cb.toggle()
        assert cb.isChecked() is True
        cb.toggle()
        assert cb.isChecked() is False

    def test_toggle_emits_signal(self, app_instance, qtbot):
        cb = CustomCheckBox()
        with qtbot.waitSignal(cb.stateChanged, raising=False):
            cb.toggle()

    def test_fixed_size(self, app_instance):
        cb = CustomCheckBox()
        assert cb.width() == 16
        assert cb.height() == 16

    def test_has_pointing_hand_cursor(self, app_instance):
        cb = CustomCheckBox()
        assert cb.cursor().shape() == Qt.CursorShape.PointingHandCursor


class TestCheckboxWidget:
    def test_creates_with_default_values(self, app_instance):
        w = CheckboxWidget(obj_id=1)
        assert w.obj_id == 1
        assert w._checked is False
        assert w._text == ""

    def test_creates_with_custom_values(self, app_instance):
        w = CheckboxWidget(obj_id=42, text="hello", checked=True)
        assert w.obj_id == 42
        assert w._checked is True
        assert w._text == "hello"

    def test_checkbox_is_custom_widget(self, app_instance):
        w = CheckboxWidget(obj_id=1)
        assert isinstance(w._checkbox, CustomCheckBox)

    def test_check_emits_changed_signal(self, app_instance, qtbot):
        w = CheckboxWidget(obj_id=1, text="test")
        with qtbot.waitSignal(w.changed, raising=False) as blocker:
            w._checkbox.setChecked(True)
        assert blocker.signal_triggered is True
        assert blocker.args == [1, True, "test"]

    def test_uncheck_emits_changed_signal(self, app_instance, qtbot):
        w = CheckboxWidget(obj_id=1, text="test", checked=True)
        with qtbot.waitSignal(w.changed, raising=False) as blocker:
            w._checkbox.setChecked(False)
        assert blocker.signal_triggered is True
        assert blocker.args == [1, False, "test"]

    def test_text_change_emits_changed_signal(self, app_instance, qtbot):
        w = CheckboxWidget(obj_id=1, text="old")
        with qtbot.waitSignal(w.changed, raising=False) as blocker:
            w._text_edit.setText("new")
        assert blocker.signal_triggered is True
        assert blocker.args == [1, False, "new"]

    def test_get_data(self, app_instance):
        w = CheckboxWidget(obj_id=1, text="buy milk", checked=True)
        data = w.get_data()
        assert data == {"text": "buy milk", "checked": True}

    def test_set_data(self, app_instance):
        w = CheckboxWidget(obj_id=1)
        w.set_data({"text": "eggs", "checked": True})
        assert w._text_edit.text() == "eggs"
        assert w._checkbox.isChecked() is True

    def test_set_data_defaults(self, app_instance):
        w = CheckboxWidget(obj_id=1)
        w.set_data({})
        assert w._text_edit.text() == ""
        assert w._checkbox.isChecked() is False

    def test_strikethrough_when_checked(self, app_instance):
        w = CheckboxWidget(obj_id=1, checked=True)
        style = w._text_edit.styleSheet()
        assert "line-through" in style

    def test_no_strikethrough_when_unchecked(self, app_instance):
        w = CheckboxWidget(obj_id=1, checked=False)
        style = w._text_edit.styleSheet()
        assert "line-through" not in style

    def test_checked_text_color_is_gray(self, app_instance):
        w = CheckboxWidget(obj_id=1, checked=True)
        style = w._text_edit.styleSheet()
        assert "#9CA3AF" in style

    def test_unchecked_text_color_is_dark(self, app_instance):
        w = CheckboxWidget(obj_id=1, checked=False)
        style = w._text_edit.styleSheet()
        assert "#2E2B2B" in style

    def test_delete_button_exists(self, app_instance):
        w = CheckboxWidget(obj_id=1)
        assert w._delete_btn is not None
        assert w._delete_btn.text() == "×"

    def test_delete_emits_signal(self, app_instance, qtbot):
        w = CheckboxWidget(obj_id=7)
        with qtbot.waitSignal(w.delete_requested, raising=False) as blocker:
            w._delete_btn.click()
        assert blocker.signal_triggered is True
        assert blocker.args == [7]

    def test_enter_pressed_emits_signal(self, app_instance, qtbot):
        w = CheckboxWidget(obj_id=3)
        with qtbot.waitSignal(w.enter_pressed, raising=False) as blocker:
            w._text_edit.returnPressed.emit()
        assert blocker.signal_triggered is True
        assert blocker.args == [3]

    def test_focus_text_sets_focus_policy(self, app_instance):
        w = CheckboxWidget(obj_id=1)
        assert w._text_edit.focusPolicy() != Qt.FocusPolicy.NoFocus


class TestChecklistDeleteButton:
    def test_delete_button_exists(self, app_instance):
        cl = ChecklistWidget(checklist_id=1, page_id=1)
        assert cl._delete_btn is not None
        assert cl._delete_btn.text() == "×"

    def test_delete_button_click_passes_event_filter(self, app_instance, qtbot):
        cl = ChecklistWidget(checklist_id=1, page_id=1)
        with qtbot.waitSignal(cl.object_delete_requested, raising=False) as blocker:
            cl._delete_btn.click()
        assert blocker.signal_triggered is True
        assert blocker.args == [1]

    def test_delete_button_not_consumed_by_drag(self, app_instance):
        cl = ChecklistWidget(checklist_id=5, page_id=1)
        btn = cl._delete_btn
        pos = btn.mapTo(cl, QPoint(btn.width() // 2, btn.height() // 2))
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(pos),
            QPointF(pos),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        result = cl.eventFilter(btn, event)
        assert (
            result is False
        ), "Delete button click should not be consumed by drag logic"


def _make_mouse_event(
    event_type, pos, button=Qt.MouseButton.LeftButton, buttons=Qt.MouseButton.NoButton
):
    return QMouseEvent(
        event_type,
        QPointF(pos),
        QPointF(pos),
        button,
        buttons,
        Qt.KeyboardModifier.NoModifier,
    )


def _make_key_event(key, modifiers=Qt.KeyboardModifier.NoModifier):
    return QKeyEvent(QEvent.Type.KeyPress, key, modifiers)


class TestChecklistWidgetSaveMeta:
    def test_save_meta_updates_existing(self, app_instance):
        page_id = PageRepo.create(Page(title="Test Page"))
        cl = ChecklistWidget(checklist_id=5, page_id=page_id)
        cl.move(10, 20)
        cl.resize(250, 150)

        existing = PageObject(
            page_id=page_id,
            object_type="checklist_meta",
            content=json.dumps({"x": 0, "y": 0, "width": 100, "height": 100}),
            sort_order=550,
        )
        existing.id = PageObjectRepo.create(existing)

        cl._save_meta()

        updated = PageObjectRepo.get_meta(page_id, 5)
        assert updated is not None
        data = json.loads(updated.content)
        assert data["x"] == 10
        assert data["y"] == 20
        assert updated.id == existing.id

    def test_save_meta_creates_when_none(self, app_instance):
        page_id = PageRepo.create(Page(title="Test Page"))
        cl = ChecklistWidget(checklist_id=3, page_id=page_id)
        cl.move(5, 15)
        cl.resize(200, 120)

        cl._save_meta()

        meta = PageObjectRepo.get_meta(page_id, 3)
        assert meta is not None
        data = json.loads(meta.content)
        assert data["x"] == 5
        assert data["y"] == 15


class TestChecklistWidgetDeleteChecklist:
    def test_delete_checklist_removes_items_and_emits(self, app_instance, qtbot):
        page_id = PageRepo.create(Page(title="P"))
        cl = ChecklistWidget(checklist_id=7, page_id=page_id)
        cl.show()

        w1 = cl._add_item(text="a")
        w2 = cl._add_item(text="b")
        obj_ids = [w1.obj_id, w2.obj_id]

        with qtbot.waitSignal(cl.object_delete_requested, raising=False) as blocker:
            cl._delete_checklist()

        assert blocker.signal_triggered is True
        assert blocker.args == [7]

        for oid in obj_ids:
            assert PageObjectRepo.get_by_id(oid) is None


class TestResizableMixinEdgeCursor:
    def test_mouse_move_at_edge_changes_cursor(self, app_instance):
        cl = ChecklistWidget(checklist_id=46, page_id=1)
        cl.resize(400, 300)
        cl.show()

        w, h = cl.width(), cl.height()
        pos = QPoint(w - 3, h // 2)
        event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(pos),
            QPointF(cl.mapToGlobal(pos)),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        cl.mouseMoveEvent(event)

        assert cl.cursor().shape() != Qt.CursorShape.ArrowCursor

    def test_mouse_move_away_resets_cursor(self, app_instance):
        cl = ChecklistWidget(checklist_id=47, page_id=1)
        cl.resize(400, 300)
        cl.show()

        pos = QPoint(200, 150)
        event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(pos),
            QPointF(cl.mapToGlobal(pos)),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        cl.mouseMoveEvent(event)

        assert cl.cursor().shape() == Qt.CursorShape.ArrowCursor
