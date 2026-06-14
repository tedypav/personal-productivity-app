from unittest.mock import MagicMock

import pytest

from src.controllers.page_controller import PageController


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def controller(mock_repo):
    return PageController(page_repo=mock_repo)


class TestPageController:
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

    def test_rename_page(self, controller, mock_repo):
        mock_page = MagicMock()
        mock_page.title = "Old Title"
        mock_repo.get_by_id.return_value = mock_page
        controller.rename_page(1, "New Title")
        assert mock_page.title == "New Title"
        mock_repo.update.assert_called_once()

    def test_rename_page_not_found(self, controller, mock_repo):
        mock_repo.get_by_id.return_value = None
        controller.rename_page(999, "New Title")
        mock_repo.update.assert_not_called()

    def test_get_page(self, controller, mock_repo):
        mock_repo.get_by_id.return_value = MagicMock()
        result = controller.get_page(1)
        assert result is not None
        mock_repo.get_by_id.assert_called_once_with(1)

    def test_get_children(self, controller, mock_repo):
        mock_repo.get_children.return_value = [MagicMock(), MagicMock()]
        result = controller.get_children(1)
        assert len(result) == 2
        mock_repo.get_children.assert_called_once_with(1)

    def test_bulk_create_named(self, controller, mock_repo):
        count = controller.bulk_create_named("Test", 3)
        assert count == 3
        assert mock_repo.create.call_count == 3

    def test_bulk_create_named_empty_name(self, controller, mock_repo):
        count = controller.bulk_create_named("", 3)
        assert count == 3
