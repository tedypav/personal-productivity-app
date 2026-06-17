from datetime import date

from PyQt6.QtCore import QDate

from src.ui.bulk_create_dialog import (
    BulkCreateDialog,
    _style_calendar_dates,
    generate_titles,
)


class TestStyleCalendarDates:
    def test_applies_format_to_calendar(self, app_instance):
        from PyQt6.QtWidgets import QDateEdit

        de = QDateEdit()
        de.setCalendarPopup(True)
        _style_calendar_dates(de)
        cal = de.calendarWidget()
        assert cal is not None


class TestBulkCreateDialogInit:
    def test_creates_dialog(self, app_instance):
        dialog = BulkCreateDialog(None, {})
        assert dialog.windowTitle() == "Bulk Create Pages"

    def test_default_mode_is_days(self, app_instance):
        dialog = BulkCreateDialog(None, {})
        assert dialog._mode_combo.currentText() == "Days"

    def test_week_start_hidden_by_default(self, app_instance):
        dialog = BulkCreateDialog(None, {})
        dialog.show()
        assert not dialog._week_start_label.isVisible()
        assert not dialog._week_start_combo.isVisible()

    def test_settings_week_start_applied(self, app_instance):
        dialog = BulkCreateDialog(None, {"week_start_day": "Wednesday"})
        assert dialog._week_start_combo.currentText() == "Wednesday"

    def test_titles_empty_initially(self, app_instance):
        dialog = BulkCreateDialog(None, {})
        assert dialog.get_titles() == []

    def test_selected_folder_id_stored(self, app_instance):
        dialog = BulkCreateDialog(None, {}, selected_folder_id=42)
        assert dialog._selected_folder_id == 42


class TestBulkCreateDialogModeChange:
    def test_weeks_shows_week_start(self, app_instance):
        dialog = BulkCreateDialog(None, {})
        dialog.show()
        dialog._mode_combo.setCurrentText("Weeks")
        assert dialog._week_start_label.isVisible()
        assert dialog._week_start_combo.isVisible()

    def test_days_hides_week_start(self, app_instance):
        dialog = BulkCreateDialog(None, {})
        dialog.show()
        dialog._mode_combo.setCurrentText("Weeks")
        dialog._mode_combo.setCurrentText("Days")
        assert not dialog._week_start_label.isVisible()
        assert not dialog._week_start_combo.isVisible()

    def test_years_hides_week_start(self, app_instance):
        dialog = BulkCreateDialog(None, {})
        dialog.show()
        dialog._mode_combo.setCurrentText("Years")
        assert not dialog._week_start_label.isVisible()


class TestBulkCreateDialogEndDateUpdate:
    def test_days_end_is_plus_one(self, app_instance):
        dialog = BulkCreateDialog(None, {})
        dialog._start_date.setDate(QDate(2026, 6, 10))
        dialog._update_end_date()
        assert dialog._end_date.date().toPyDate() == date(2026, 6, 11)

    def test_weeks_end_is_plus_seven(self, app_instance):
        dialog = BulkCreateDialog(None, {})
        dialog._mode_combo.setCurrentText("Weeks")
        dialog._start_date.setDate(QDate(2026, 6, 10))
        dialog._update_end_date()
        assert dialog._end_date.date().toPyDate() == date(2026, 6, 17)

    def test_years_end_is_plus_one_year(self, app_instance):
        dialog = BulkCreateDialog(None, {})
        dialog._mode_combo.setCurrentText("Years")
        dialog._start_date.setDate(QDate(2026, 6, 10))
        dialog._update_end_date()
        assert dialog._end_date.date().toPyDate() == date(2027, 6, 10)


class TestBulkCreateDialogAccept:
    def test_accept_generates_days_titles(self, app_instance):
        dialog = BulkCreateDialog(None, {})
        dialog._mode_combo.setCurrentText("Days")
        dialog._start_date.setDate(QDate(2026, 6, 1))
        dialog._end_date.setDate(QDate(2026, 6, 3))
        dialog.accept()
        assert len(dialog.get_titles()) == 3

    def test_accept_generates_weeks_titles(self, app_instance):
        dialog = BulkCreateDialog(None, {})
        dialog._mode_combo.setCurrentText("Weeks")
        dialog._start_date.setDate(QDate(2026, 6, 1))
        dialog._end_date.setDate(QDate(2026, 6, 15))
        dialog.accept()
        assert len(dialog.get_titles()) >= 2

    def test_accept_generates_years_titles(self, app_instance):
        dialog = BulkCreateDialog(None, {})
        dialog._mode_combo.setCurrentText("Years")
        dialog._start_date.setDate(QDate(2024, 1, 1))
        dialog._end_date.setDate(QDate(2026, 12, 31))
        dialog.accept()
        assert dialog.get_titles() == ["2024", "2025", "2026"]


class TestGenerateTitlesEdgeCases:
    def test_unknown_mode_returns_empty(self):
        result = generate_titles("Invalid", date(2026, 6, 1), date(2026, 6, 3))
        assert result == []

    def test_weeks_default_monday(self):
        result = generate_titles("Weeks", date(2026, 6, 1), date(2026, 6, 15))
        assert len(result) >= 2

    def test_years_single_year(self):
        result = generate_titles("Years", date(2026, 1, 1), date(2026, 12, 31))
        assert result == ["2026"]
