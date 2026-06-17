from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.controllers.page_controller import PageController


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def controller(mock_repo):
    return PageController(page_repo=mock_repo)


@pytest.fixture
def controller_with_undo(mock_repo):
    mock_undo = MagicMock()
    return PageController(page_repo=mock_repo, undo_manager=mock_undo), mock_undo


class TestPageControllerCreate:
    def test_create_page(self, controller, mock_repo):
        mock_repo.create.return_value = 1
        page_id = controller.create_page("Test Page")
        assert page_id == 1
        mock_repo.create.assert_called_once()

    def test_create_page_with_parent(self, controller, mock_repo):
        mock_repo.create.return_value = 2
        page_id = controller.create_page("Child Page", parent_id=1)
        assert page_id == 2
        call_args = mock_repo.create.call_args[0][0]
        assert call_args.parent_id == 1

    def test_create_page_strips_title(self, controller, mock_repo):
        mock_repo.create.return_value = 3
        controller.create_page("  Test Page  ")
        call_args = mock_repo.create.call_args[0][0]
        assert call_args.title == "Test Page"

    def test_create_page_emits_signals(self, controller, mock_repo):
        mock_repo.create.return_value = 5
        created_ids = []
        changed = []
        controller.page_created.connect(lambda x: created_ids.append(x))
        controller.tree_changed.connect(lambda: changed.append(True))
        controller.create_page("Signal Test")
        assert 5 in created_ids
        assert len(changed) == 1


class TestPageControllerRename:
    def test_rename_page(self, controller, mock_repo):
        mock_page = MagicMock()
        mock_page.title = "Old Title"
        mock_repo.get_by_id.return_value = mock_page
        controller.rename_page(1, "New Title")
        assert mock_page.title == "New Title"
        mock_repo.update.assert_called_once()

    def test_rename_page_strips_title(self, controller, mock_repo):
        mock_page = MagicMock()
        mock_page.title = "Old"
        mock_repo.get_by_id.return_value = mock_page
        controller.rename_page(1, "  New  ")
        assert mock_page.title == "New"

    def test_rename_page_not_found(self, controller, mock_repo):
        mock_repo.get_by_id.return_value = None
        controller.rename_page(999, "New Title")
        mock_repo.update.assert_not_called()


class TestPageControllerGet:
    def test_get_page(self, controller, mock_repo):
        mock_repo.get_by_id.return_value = MagicMock()
        result = controller.get_page(1)
        assert result is not None
        mock_repo.get_by_id.assert_called_once_with(1)

    def test_get_page_not_found(self, controller, mock_repo):
        mock_repo.get_by_id.return_value = None
        result = controller.get_page(999)
        assert result is None

    def test_get_children(self, controller, mock_repo):
        mock_repo.get_children.return_value = [MagicMock(), MagicMock()]
        result = controller.get_children(1)
        assert len(result) == 2
        mock_repo.get_children.assert_called_once_with(1)

    def test_get_children_empty(self, controller, mock_repo):
        mock_repo.get_children.return_value = []
        result = controller.get_children(1)
        assert result == []

    def test_get_all_pages(self, controller, mock_repo):
        mock_repo.get_all.return_value = [MagicMock(), MagicMock(), MagicMock()]
        result = controller.get_all_pages()
        assert len(result) == 3
        mock_repo.get_all.assert_called_once()


class TestPageControllerDelete:
    def test_delete_page(self, controller_with_undo, mock_repo):
        controller, mock_undo = controller_with_undo
        with patch("src.undo_manager.capture_page_tree") as mock_capture:
            mock_capture.return_value = {"type": "page", "page": {"id": 1}}
            controller.delete_page(1)
            mock_capture.assert_called_once_with(1)
            mock_undo.push.assert_called_once()
            mock_repo.delete.assert_called_once_with(1)

    def test_delete_page_no_data(self, controller_with_undo, mock_repo):
        controller, mock_undo = controller_with_undo
        with patch("src.undo_manager.capture_page_tree") as mock_capture:
            mock_capture.return_value = None
            controller.delete_page(1)
            mock_undo.push.assert_not_called()
            mock_repo.delete.assert_called_once_with(1)

    def test_delete_page_emits_signals(self, controller_with_undo, mock_repo):
        controller, mock_undo = controller_with_undo
        deleted_ids = []
        controller.page_deleted.connect(lambda x: deleted_ids.append(x))
        with patch("src.undo_manager.capture_page_tree") as mock_capture:
            mock_capture.return_value = None
            controller.delete_page(7)
            assert 7 in deleted_ids


class TestPageControllerGetUndo:
    def test_get_undo_with_init(self, controller_with_undo):
        controller, mock_undo = controller_with_undo
        result = controller._get_undo()
        assert result is mock_undo

    def test_get_undo_lazy_load(self, controller, mock_repo):
        assert controller._undo is None
        with patch("src.undo_manager.undo_manager") as mock_um:
            result = controller._get_undo()
            assert result is mock_um


class TestPageControllerBulkCreate:
    def test_bulk_create_named(self, controller, mock_repo):
        count = controller.bulk_create_named("Test", 3)
        assert count == 3
        assert mock_repo.create.call_count == 3

    def test_bulk_create_named_empty_name(self, controller, mock_repo):
        count = controller.bulk_create_named("", 3)
        assert count == 3

    def test_bulk_create_named_zero_count(self, controller, mock_repo):
        count = controller.bulk_create_named("Test", 0)
        assert count == 0
        mock_repo.create.assert_not_called()

    def test_bulk_create_named_titles(self, controller, mock_repo):
        controller.bulk_create_named("Task", 2)
        titles = [call[0][0].title for call in mock_repo.create.call_args_list]
        assert titles == ["Task 1", "Task 2"]

    def test_bulk_create_days(self, controller, mock_repo):
        count = controller.bulk_create_days(date(2026, 6, 1), date(2026, 6, 3))
        assert count == 3
        assert mock_repo.create.call_count == 3
        titles = [call[0][0].title for call in mock_repo.create.call_args_list]
        assert titles == ["2026-06-01", "2026-06-02", "2026-06-03"]

    def test_bulk_create_days_single(self, controller, mock_repo):
        count = controller.bulk_create_days(date(2026, 6, 1), date(2026, 6, 1))
        assert count == 1

    def test_bulk_create_days_empty_range(self, controller, mock_repo):
        count = controller.bulk_create_days(date(2026, 6, 5), date(2026, 6, 3))
        assert count == 0
        mock_repo.create.assert_not_called()

    def test_bulk_create_weeks(self, controller, mock_repo):
        count = controller.bulk_create_weeks(date(2026, 6, 1), date(2026, 6, 15))
        assert count >= 2
        titles = [call[0][0].title for call in mock_repo.create.call_args_list]
        for title in titles:
            assert " - " in title

    def test_bulk_create_weeks_sunday_start(self, controller, mock_repo):
        count = controller.bulk_create_weeks(
            date(2026, 6, 1), date(2026, 6, 15), "Sunday"
        )
        assert count >= 2

    def test_bulk_create_weeks_default_monday(self, controller, mock_repo):
        count = controller.bulk_create_weeks(date(2026, 6, 1), date(2026, 6, 15))
        assert count >= 2

    def test_bulk_create_years(self, controller, mock_repo):
        count = controller.bulk_create_years(date(2024, 1, 1), date(2026, 12, 31))
        assert count == 3
        titles = [call[0][0].title for call in mock_repo.create.call_args_list]
        assert titles == ["2024", "2025", "2026"]

    def test_bulk_create_years_single(self, controller, mock_repo):
        count = controller.bulk_create_years(date(2026, 1, 1), date(2026, 12, 31))
        assert count == 1
        titles = [call[0][0].title for call in mock_repo.create.call_args_list]
        assert titles == ["2026"]

    def test_bulk_create_days_emits_signal(self, controller, mock_repo):
        counts = []
        controller.pages_bulk_created.connect(lambda x: counts.append(x))
        controller.bulk_create_days(date(2026, 6, 1), date(2026, 6, 2))
        assert 2 in counts

    def test_bulk_create_named_emits_signal(self, controller, mock_repo):
        counts = []
        controller.pages_bulk_created.connect(lambda x: counts.append(x))
        controller.bulk_create_named("X", 4)
        assert 4 in counts
