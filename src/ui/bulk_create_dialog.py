from datetime import timedelta

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor, QTextCharFormat
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from src.ui.dialogs import create_dialog_header

WEEK_DAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


def _style_calendar_dates(date_edit):
    cal = date_edit.calendarWidget()
    if cal:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#CFA6D6"))
        cal.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, fmt)
        cal.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, fmt)


def generate_titles(mode, start, end, week_start_day="Monday"):
    """Generate page titles for bulk creation based on mode and date range."""
    titles = []
    if mode == "Days":
        current = start
        while current <= end:
            titles.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
    elif mode == "Weeks":
        target_wd = WEEK_DAYS.get(week_start_day, 0)
        current = start
        while current.weekday() != target_wd:
            current -= timedelta(days=1)
        while current <= end:
            week_end = current + timedelta(days=6)
            date_str = (
                f"{current.strftime('%Y-%m-%d')}" f" - {week_end.strftime('%Y-%m-%d')}"
            )
            titles.append(date_str)
            current += timedelta(weeks=1)
    elif mode == "Years":
        for year in range(start.year, end.year + 1):
            titles.append(str(year))
    return titles


class BulkCreateDialog(QDialog):
    def __init__(self, parent, settings, selected_folder_id=None):
        super().__init__(parent)
        self.setWindowTitle("Bulk Create Pages")
        self._settings = settings
        self._selected_folder_id = selected_folder_id
        self._titles = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addLayout(create_dialog_header("Bulk Create Pages"))

        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Days", "Weeks", "Years"])
        layout.addWidget(QLabel("Mode:"))
        layout.addWidget(self._mode_combo)

        self._start_date = QDateEdit()
        self._start_date.setObjectName("bulkDateEdit")
        self._start_date.setCalendarPopup(True)
        self._start_date.setDate(QDate.currentDate())
        self._start_date.setDisplayFormat("yyyy-MM-dd")
        self._start_date.calendarWidget().setObjectName("bulkCalendar")
        _style_calendar_dates(self._start_date)
        layout.addWidget(QLabel("Start date:"))
        layout.addWidget(self._start_date)

        self._end_label = QLabel("End date:")
        self._end_date = QDateEdit()
        self._end_date.setObjectName("bulkDateEdit")
        self._end_date.setCalendarPopup(True)
        self._end_date.setDate(QDate.currentDate())
        self._end_date.setDisplayFormat("yyyy-MM-dd")
        self._end_date.calendarWidget().setObjectName("bulkCalendar")
        _style_calendar_dates(self._end_date)
        layout.addWidget(self._end_label)
        layout.addWidget(self._end_date)

        self._week_start_label = QLabel("Week starts on:")
        self._week_start_combo = QComboBox()
        self._week_start_combo.addItems(list(WEEK_DAYS.keys()))
        self._week_start_combo.setCurrentText(
            self._settings.get("week_start_day", "Monday")
        )
        self._week_start_label.setVisible(False)
        self._week_start_combo.setVisible(False)
        layout.addWidget(self._week_start_label)
        layout.addWidget(self._week_start_combo)

        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_mode_changed(self, index):
        is_weeks = self._mode_combo.currentText() == "Weeks"
        self._week_start_label.setVisible(is_weeks)
        self._week_start_combo.setVisible(is_weeks)
        self._update_end_date()

    def _update_end_date(self):
        mode = self._mode_combo.currentText()
        if mode == "Days":
            self._end_date.setDate(self._start_date.date().addDays(1))
        elif mode == "Weeks":
            self._end_date.setDate(self._start_date.date().addDays(7))
        elif mode == "Years":
            self._end_date.setDate(self._start_date.date().addYears(1))

    def get_titles(self):
        """Return the list of generated page titles after the dialog is accepted."""
        return self._titles

    def accept(self):
        """Generate titles from mode and date range, then accept the dialog."""
        mode = self._mode_combo.currentText()
        start = self._start_date.date().toPyDate()
        end = self._end_date.date().toPyDate()
        week_start = self._week_start_combo.currentText()
        self._titles = generate_titles(mode, start, end, week_start)
        super().accept()
