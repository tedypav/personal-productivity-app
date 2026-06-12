from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)


class CheckboxWidget(QWidget):
    """A single checkbox item with editable text and delete button."""

    changed = pyqtSignal(int, bool, str)
    delete_requested = pyqtSignal(int)

    def __init__(self, obj_id: int, text: str = "", checked: bool = False, parent=None):
        super().__init__(parent)
        self.obj_id = obj_id
        self._text = text
        self._checked = checked
        self.setStyleSheet("background: transparent;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        self._checkbox = QCheckBox()
        self._checkbox.setChecked(self._checked)
        self._checkbox.stateChanged.connect(self._on_check_changed)
        self._checkbox.setStyleSheet(
            "QCheckBox { spacing: 6px; background: transparent; }"
            "QCheckBox::indicator {"
            " width: 18px; height: 18px;"
            " border: 2px solid #F7D1DC; border-radius: 9px;"
            " background: #FFFFFF; }"
            "QCheckBox::indicator:checked {"
            " background: #CFA6D6; border: 2px solid #CFA6D6; }"
            "QCheckBox::indicator:hover { border-color: #CFA6D6; }"
        )
        layout.addWidget(self._checkbox)

        self._text_edit = QLineEdit(self._text)
        self._text_edit.setPlaceholderText("Type something...")
        self._text_edit.setStyleSheet(
            "QLineEdit { border: none; background: transparent;"
            " font-size: 13px; color: #2E2B2B;"
            " font-family: 'Inter', sans-serif; padding: 2px 0; }"
        )
        self._text_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._text_edit, 1)

        self._delete_btn = QPushButton("×")
        self._delete_btn.setFixedSize(20, 20)
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_btn.setStyleSheet(
            "QPushButton { border: none; font-size: 14px; color: #9CA3AF;"
            " border-radius: 10px; background: transparent; }"
            " QPushButton:hover { color: #EF4444; background: #FEE2E2; }"
        )
        self._delete_btn.clicked.connect(
            lambda: self.delete_requested.emit(self.obj_id)
        )
        layout.addWidget(self._delete_btn)

        self._update_style()

    def _on_check_changed(self, state):
        self._checked = state == Qt.CheckState.Checked.value
        self._update_style()
        self.changed.emit(self.obj_id, self._checked, self._text_edit.text())

    def _on_text_changed(self, text):
        self._text = text
        self.changed.emit(self.obj_id, self._checked, text)

    def _update_style(self):
        if self._checked:
            self._text_edit.setStyleSheet(
                "QLineEdit { border: none; background: transparent;"
                " font-size: 13px; color: #9CA3AF;"
                " font-family: 'Inter', sans-serif; padding: 2px 0;"
                " text-decoration: line-through; }"
            )
        else:
            self._text_edit.setStyleSheet(
                "QLineEdit { border: none; background: transparent;"
                " font-size: 13px; color: #2E2B2B;"
                " font-family: 'Inter', sans-serif; padding: 2px 0; }"
            )

    def get_data(self) -> dict:
        return {
            "text": self._text_edit.text(),
            "checked": self._checked,
        }

    def set_data(self, data: dict):
        self._text_edit.setText(data.get("text", ""))
        self._checkbox.setChecked(data.get("checked", False))
