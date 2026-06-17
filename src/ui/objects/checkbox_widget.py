from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QToolButton,
    QWidget,
)


class CustomCheckBox(QWidget):
    """A custom-painted checkbox indicator that replaces the native QCheckBox."""

    stateChanged = pyqtSignal(int)

    _SIZE = 16
    _BORDER_RADIUS = 3
    _BORDER_WIDTH = 2
    _UNCHECKED_BORDER = QColor("#E0D6D8")
    _UNCHECKED_BG = QColor("#FFFFFF")
    _CHECKED_BG = QColor("#CFA6D6")
    _CHECKED_BORDER = QColor("#CFA6D6")
    _CHECKMARK_COLOR = QColor("#FFFFFF")

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(self._SIZE, self._SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self) -> bool:
        """Return whether the checkbox is checked."""
        return self._checked

    def setChecked(self, checked: bool) -> None:
        """Set the checked state and emit stateChanged if it changed."""
        if self._checked != checked:
            self._checked = checked
            self.update()
            if checked:
                val = Qt.CheckState.Checked.value
            else:
                val = Qt.CheckState.Unchecked.value
            self.stateChanged.emit(val)

    def toggle(self) -> None:
        """Toggle the checkbox state."""
        self.setChecked(not self._checked)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press to toggle on left-click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        """Custom-paint the checkbox indicator with rounded rect and checkmark."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._checked:
            brush = QBrush(self._CHECKED_BG)
            pen = QPen(self._CHECKED_BORDER, self._BORDER_WIDTH)
        else:
            brush = QBrush(self._UNCHECKED_BG)
            pen = QPen(self._UNCHECKED_BORDER, self._BORDER_WIDTH)

        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawRoundedRect(
            self._BORDER_WIDTH // 2,
            self._BORDER_WIDTH // 2,
            self._SIZE - self._BORDER_WIDTH,
            self._SIZE - self._BORDER_WIDTH,
            self._BORDER_RADIUS,
            self._BORDER_RADIUS,
        )

        if self._checked:
            check_pen = QPen(
                self._CHECKMARK_COLOR,
                2.2,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
            painter.setPen(check_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            path = QPainterPath()
            path.moveTo(3.5, 8.5)
            path.lineTo(7, 12.5)
            path.lineTo(12.5, 4)
            painter.drawPath(path)

        painter.end()


class CheckboxWidget(QWidget):
    """A single checkbox item with editable text and delete button."""

    changed = pyqtSignal(int, bool, str)
    delete_requested = pyqtSignal(int)
    enter_pressed = pyqtSignal(int)

    def __init__(self, obj_id: int, text: str = "", checked: bool = False, parent=None):
        super().__init__(parent)
        self.obj_id = obj_id
        self._text = text
        self._checked = checked
        self.setObjectName("checkboxWidget")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self._checkbox = CustomCheckBox(checked=self._checked)
        self._checkbox.stateChanged.connect(self._on_check_changed)
        layout.addWidget(self._checkbox)

        self._text_edit = QLineEdit(self._text)
        self._text_edit.setObjectName("checkboxText")
        self._text_edit.setPlaceholderText("Type something...")
        self._text_edit.textChanged.connect(self._on_text_changed)
        self._text_edit.returnPressed.connect(
            lambda: self.enter_pressed.emit(self.obj_id)
        )
        layout.addWidget(self._text_edit, 1)

        self._delete_btn = QToolButton()
        self._delete_btn.setObjectName("checkboxDeleteBtn")
        self._delete_btn.setText("×")
        self._delete_btn.setFixedSize(26, 26)
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
        """Return the checkbox state as a dictionary."""
        return {
            "text": self._text_edit.text(),
            "checked": self._checked,
        }

    def set_data(self, data: dict):
        """Restore checkbox state from a dictionary."""
        self._text_edit.setText(data.get("text", ""))
        self._checkbox.setChecked(data.get("checked", False))

    def focus_text(self):
        """Set keyboard focus to the text input field."""
        self._text_edit.setFocus()
