from PyQt6.QtCore import Qt

from src.ui.objects.checkbox_widget import CheckboxWidget, CustomCheckBox


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
