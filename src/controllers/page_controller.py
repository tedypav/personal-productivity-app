"""Page business logic controller — CRUD, bulk creation, undo."""

from __future__ import annotations

from datetime import date

from PyQt6.QtCore import QObject, pyqtSignal

from src.models.page import Page
from src.repositories.page_repo import PageRepo


class PageController(QObject):
    """Handles page business logic, separated from UI."""

    page_created = pyqtSignal(int)
    page_deleted = pyqtSignal(int)
    pages_bulk_created = pyqtSignal(int)
    page_renamed = pyqtSignal(int, str)
    tree_changed = pyqtSignal()

    def __init__(
        self,
        page_repo: PageRepo | None = None,
        undo_manager=None,
    ) -> None:
        super().__init__()
        self._repo = page_repo or PageRepo()
        self._undo = undo_manager

    def _get_undo(self):
        if self._undo is None:
            from src.undo_manager import undo_manager

            self._undo = undo_manager
        return self._undo

    def create_page(self, title: str, parent_id: int | None = None) -> int:
        """Create a new page and return its ID."""
        page = Page(title=title.strip(), parent_id=parent_id)
        page_id = self._repo.create(page)
        self.page_created.emit(page_id)
        self.tree_changed.emit()
        return page_id

    def delete_page(self, page_id: int) -> None:
        """Delete a page, capturing it for undo first."""
        from src.undo_manager import capture_page_tree

        data = capture_page_tree(page_id)
        if data:
            data["type"] = "page"
            self._get_undo().push(data)
        self._repo.delete(page_id)
        self.page_deleted.emit(page_id)
        self.tree_changed.emit()

    def rename_page(self, page_id: int, new_title: str) -> None:
        """Rename a page, stripping whitespace from the title."""
        page = self._repo.get_by_id(page_id)
        if page:
            page.title = new_title.strip()
            self._repo.update(page)
            self.page_renamed.emit(page_id, new_title)
            self.tree_changed.emit()

    def get_page(self, page_id: int) -> Page | None:
        """Return a page by ID, or None if not found."""
        return self._repo.get_by_id(page_id)

    def get_children(self, page_id: int) -> list[Page]:
        """Return all child pages of the given parent."""
        return self._repo.get_children(page_id)

    def get_all_pages(self) -> list[Page]:
        """Return all pages in the database."""
        return self._repo.get_all()

    def bulk_create_days(self, start_date: date, end_date: date) -> int:
        """Create one page per day in the given date range. Returns count."""
        from datetime import timedelta

        count = 0
        current = start_date
        while current <= end_date:
            title = current.strftime("%Y-%m-%d")
            page = Page(title=title, page_type="page")
            self._repo.create(page)
            current += timedelta(days=1)
            count += 1
        self.pages_bulk_created.emit(count)
        self.tree_changed.emit()
        return count

    def bulk_create_weeks(
        self,
        start_date: date,
        end_date: date,
        week_start_day: str = "Monday",
    ) -> int:
        """Create one page per week, snapped to the chosen start day. Returns count."""
        from datetime import timedelta

        week_days = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }
        target_day = week_days.get(week_start_day, 0)

        count = 0
        current = start_date
        while current <= end_date:
            days_offset = (current.weekday() - target_day) % 7
            start_of_week = current - timedelta(days=days_offset)
            end_of_week = start_of_week + timedelta(days=6)
            start_str = start_of_week.strftime("%Y-%m-%d")
            end_str = end_of_week.strftime("%Y-%m-%d")
            title = f"{start_str} - {end_str}"
            page = Page(title=title, page_type="page")
            self._repo.create(page)
            current = end_of_week + timedelta(days=1)
            count += 1
        self.pages_bulk_created.emit(count)
        self.tree_changed.emit()
        return count

    def bulk_create_years(self, start_date: date, end_date: date) -> int:
        """Create one page per year in the given range. Returns count."""
        count = 0
        for year in range(start_date.year, end_date.year + 1):
            page = Page(title=str(year), page_type="page")
            self._repo.create(page)
            count += 1
        self.pages_bulk_created.emit(count)
        self.tree_changed.emit()
        return count

    def bulk_create_named(self, base_name: str, count: int) -> int:
        """Create pages named 'BaseName 1', 'BaseName 2', etc. Returns count."""
        created = 0
        for i in range(1, count + 1):
            title = f"{base_name} {i}"
            page = Page(title=title, page_type="page")
            self._repo.create(page)
            created += 1
        self.pages_bulk_created.emit(created)
        self.tree_changed.emit()
        return created
