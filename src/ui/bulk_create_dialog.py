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

CALENDAR_STYLE = """
    QDateEdit {
        padding: 6px 12px;
        border: 1px solid #F0E6E8;
        border-radius: 10px;
        background: #FFFFFF;
        font-size: 13px;
        color: #2E2B2B;
        min-width: 120px;
        font-family: 'Inter', 'Poppins', sans-serif;
    }
    QDateEdit::drop-down {
        border: none;
        width: 26px;
        subcontrol-origin: padding;
        subcontrol-position: top right;
        border-radius: 13px;
        background: #FFF0F3;
    }
    QDateEdit::drop-down:hover {
        background: #FFE4EC;
    }
    QDateEdit::down-arrow {
        image: url(assets/icons/chevron_down.svg);
        width: 12px;
        height: 12px;
    }
    QCalendarWidget {
        background: #FFFFFF;
        border: 1px solid #F0E6E8;
        border-radius: 12px;
        font-family: 'Inter', 'Poppins', sans-serif;
        font-size: 10px;
    }
    QCalendarWidget QToolButton {
        color: #2E2B2B;
        background: transparent;
        border: none;
        border-radius: 6px;
        padding: 3px 6px;
        font-size: 11px;
        font-family: 'Inter', 'Poppins', sans-serif;
    }
    QCalendarWidget QToolButton:hover {
        background: #FFF0F3;
    }
    QCalendarWidget QToolButton:pressed {
        background: #F7D1DC;
    }
    QCalendarWidget QToolButton#qt_calendar_prevmonth,
    QCalendarWidget QToolButton#qt_calendar_nextmonth {
        qproperty-icon: none;
        min-width: 22px;
        font-size: 11px;
        color: #CFA6D6;
    }
    QCalendarWidget QToolButton#qt_calendar_prevmonth { qproperty-text: "<"; }
    QCalendarWidget QToolButton#qt_calendar_nextmonth { qproperty-text: ">"; }
    QCalendarWidget QToolButton#qt_calendar_prevmonth:hover,
    QCalendarWidget QToolButton#qt_calendar_nextmonth:hover {
        color: #2E2B2B;
        background: #FFF0F3;
    }
    QCalendarWidget QToolButton#qt_calendar_monthbutton,
    QCalendarWidget QToolButton#qt_calendar_yearbutton {
        font-size: 11px;
        font-weight: 600;
        min-width: 60px;
        color: #2E2B2B;
    }
    QCalendarWidget QWidget#qt_calendar_calendarview {
        background: #FFFFFF;
        border: none;
    }
    QCalendarWidget QAbstractItemView:enabled {
        color: #2E2B2B;
        background: #FFFFFF;
        selection-background-color: #CFA6D6;
        selection-color: #FFFFFF;
        font-family: 'Inter', 'Poppins', sans-serif;
        font-size: 10px;
        gridline-color: transparent;
    }
    QCalendarWidget QAbstractItemView:disabled {
        color: #D1D5DB;
    }
    QCalendarWidget QAbstractItemView:focus {
        outline: none;
    }
    QCalendarWidget QTableView {
        selection-background-color: #CFA6D6;
        selection-color: #FFFFFF;
    }
    QCalendarWidget QTableView QHeaderView::section {
        background: #FFF8F5;
        color: #6B6770;
        border: none;
        border-bottom: 1px solid #F0E6E8;
        padding: 2px;
        font-size: 9px;
        font-weight: 600;
        font-family: 'Inter', 'Poppins', sans-serif;
    }
    QCalendarWidget QWidget#qt_calendar_navigationbar {
        background: #FFF8F5;
        border-top: 1px solid #F0E6E8;
        border-radius: 0 0 12px 12px;
        padding: 2px;
    }
    QCalendarWidget QCalendarDayWidget {
        padding: 0px;
        min-width: 24px;
        max-width: 28px;
        min-height: 18px;
        max-height: 22px;
    }
    QCalendarWidget QToolButton#qt_calendar_calendarbutton {
        qproperty-icon: none;
        min-width: 18px;
        font-size: 10px;
        color: #CFA6D6;
    }
"""

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
        self._start_date.setCalendarPopup(True)
        self._start_date.setDate(QDate.currentDate())
        self._start_date.setDisplayFormat("yyyy-MM-dd")
        self._start_date.setStyleSheet(CALENDAR_STYLE)
        _style_calendar_dates(self._start_date)
        layout.addWidget(QLabel("Start date:"))
        layout.addWidget(self._start_date)

        self._end_label = QLabel("End date:")
        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDate(QDate.currentDate())
        self._end_date.setDisplayFormat("yyyy-MM-dd")
        self._end_date.setStyleSheet(CALENDAR_STYLE)
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
        return self._titles

    def accept(self):
        mode = self._mode_combo.currentText()
        start = self._start_date.date().toPyDate()
        end = self._end_date.date().toPyDate()
        week_start = self._week_start_combo.currentText()
        self._titles = generate_titles(mode, start, end, week_start)
        super().accept()
