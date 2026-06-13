from datetime import date

from src.ui.bulk_create_dialog import generate_titles


class TestGenerateTitles:
    def test_days_single_day(self):
        result = generate_titles("Days", date(2026, 6, 1), date(2026, 6, 1))
        assert result == ["2026-06-01"]

    def test_days_range(self):
        result = generate_titles("Days", date(2026, 6, 1), date(2026, 6, 3))
        assert result == ["2026-06-01", "2026-06-02", "2026-06-03"]

    def test_days_inclusive(self):
        result = generate_titles("Days", date(2026, 6, 1), date(2026, 6, 2))
        assert len(result) == 2

    def test_weeks_monday_start(self):
        result = generate_titles("Weeks", date(2026, 6, 1), date(2026, 6, 15), "Monday")
        assert len(result) >= 2
        for title in result:
            assert " - " in title
            assert "2026-06-" in title

    def test_weeks_snaps_to_weekday(self):
        result = generate_titles("Weeks", date(2026, 6, 3), date(2026, 6, 3), "Monday")
        assert len(result) == 1
        assert result[0].startswith("2026-06-01")

    def test_weeks_sunday_start(self):
        result = generate_titles("Weeks", date(2026, 6, 1), date(2026, 6, 15), "Sunday")
        assert len(result) >= 2
        for title in result:
            assert " - " in title

    def test_years_single_year(self):
        result = generate_titles("Years", date(2026, 1, 1), date(2026, 12, 31))
        assert result == ["2026"]

    def test_years_range(self):
        result = generate_titles("Years", date(2024, 1, 1), date(2026, 12, 31))
        assert result == ["2024", "2025", "2026"]

    def test_empty_range_days(self):
        result = generate_titles("Days", date(2026, 6, 5), date(2026, 6, 3))
        assert result == []

    def test_unknown_mode(self):
        result = generate_titles("Unknown", date(2026, 6, 1), date(2026, 6, 3))
        assert result == []
