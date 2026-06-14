import json
from unittest.mock import MagicMock

import pytest

from src.controllers.checklist_controller import ChecklistController


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def controller(mock_repo):
    return ChecklistController(page_object_repo=mock_repo)


class TestChecklistController:
    def test_save_meta_creates_new(self, controller, mock_repo):
        mock_repo.get_meta.return_value = None
        mock_repo.create.return_value = 1
        controller.save_meta(1, 1, 10, 20, 200, 100, "My Checklist")
        mock_repo.create.assert_called_once()
        call_args = mock_repo.create.call_args[0][0]
        assert call_args.object_type == "checklist_meta"
        content = json.loads(call_args.content)
        assert content["x"] == 10
        assert content["y"] == 20
        assert content["title"] == "My Checklist"

    def test_save_meta_updates_existing(self, controller, mock_repo):
        mock_meta = MagicMock()
        mock_repo.get_meta.return_value = mock_meta
        controller.save_meta(1, 1, 30, 40, 250, 150, "Updated Title")
        mock_repo.update.assert_called_once_with(mock_meta)
        content = json.loads(mock_meta.content)
        assert content["x"] == 30
        assert content["title"] == "Updated Title"

    def test_load_meta_returns_data(self, controller, mock_repo):
        mock_meta = MagicMock()
        mock_meta.content = json.dumps({"x": 10, "y": 20, "title": "Test"})
        mock_repo.get_meta.return_value = mock_meta
        result = controller.load_meta(1, 1)
        assert result is not None
        assert result["x"] == 10
        assert result["title"] == "Test"

    def test_load_meta_returns_none_when_not_found(self, controller, mock_repo):
        mock_repo.get_meta.return_value = None
        result = controller.load_meta(1, 999)
        assert result is None

    def test_load_meta_handles_invalid_json(self, controller, mock_repo):
        mock_meta = MagicMock()
        mock_meta.content = "invalid json"
        mock_repo.get_meta.return_value = mock_meta
        result = controller.load_meta(1, 1)
        assert result is None

    def test_create_item(self, controller, mock_repo):
        mock_repo.create.return_value = 5
        item_id = controller.create_item(1, 1, "Buy milk")
        assert item_id == 5
        mock_repo.create.assert_called_once()
        call_args = mock_repo.create.call_args[0][0]
        assert call_args.object_type == "checkbox"
        content = json.loads(call_args.content)
        assert content["text"] == "Buy milk"
        assert content["checked"] is False

    def test_delete_item(self, controller, mock_repo):
        controller.delete_item(5)
        mock_repo.delete.assert_called_once_with(5)

    def test_update_item(self, controller, mock_repo):
        mock_obj = MagicMock()
        mock_repo.get_by_id.return_value = mock_obj
        controller.update_item(5, True, "Updated text")
        mock_repo.update.assert_called_once_with(mock_obj)
        content = json.loads(mock_obj.content)
        assert content["checked"] is True
        assert content["text"] == "Updated text"

    def test_update_item_not_found(self, controller, mock_repo):
        mock_repo.get_by_id.return_value = None
        controller.update_item(999, True, "text")
        mock_repo.update.assert_not_called()
