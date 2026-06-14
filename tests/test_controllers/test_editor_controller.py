from unittest.mock import MagicMock

import pytest

from src.controllers.editor_controller import EditorController


@pytest.fixture
def mock_page_repo():
    return MagicMock()


@pytest.fixture
def mock_obj_repo():
    return MagicMock()


@pytest.fixture
def controller(mock_page_repo, mock_obj_repo):
    return EditorController(page_repo=mock_page_repo, page_object_repo=mock_obj_repo)


class TestEditorController:
    def test_load_page(self, controller, mock_page_repo):
        mock_page = MagicMock()
        mock_page.page_type = "page"
        mock_page_repo.get_by_id.return_value = mock_page
        mock_page_repo.get_children.return_value = []
        result = controller.load_page(1)
        assert result is not None
        assert result["page"] == mock_page

    def test_load_page_folder(self, controller, mock_page_repo):
        mock_page = MagicMock()
        mock_page.page_type = "folder"
        mock_page_repo.get_by_id.return_value = mock_page
        mock_page_repo.get_children.return_value = [MagicMock(), MagicMock()]
        result = controller.load_page(1)
        assert len(result["children"]) == 2

    def test_load_page_not_found(self, controller, mock_page_repo):
        mock_page_repo.get_by_id.return_value = None
        result = controller.load_page(999)
        assert result is None

    def test_get_objects(self, controller, mock_obj_repo):
        mock_obj_repo.get_by_page.return_value = [MagicMock(), MagicMock()]
        result = controller.get_objects(1)
        assert len(result) == 2

    def test_delete_object(self, controller, mock_obj_repo):
        mock_obj = MagicMock()
        mock_obj_repo.get_by_id.return_value = mock_obj
        controller.delete_object(1)
        mock_obj_repo.delete.assert_called_once_with(1)

    def test_delete_object_not_found(self, controller, mock_obj_repo):
        mock_obj_repo.get_by_id.return_value = None
        controller.delete_object(999)
        mock_obj_repo.delete.assert_not_called()

    def test_update_object(self, controller, mock_obj_repo):
        mock_obj = MagicMock()
        mock_obj_repo.get_by_id.return_value = mock_obj
        controller.update_object(1, "new content")
        mock_obj_repo.update.assert_called_once_with(mock_obj)
        assert mock_obj.content == "new content"

    def test_create_object(self, controller, mock_obj_repo):
        mock_obj_repo.create.return_value = 10
        obj_id = controller.create_object(1, "checklist_meta", "{}")
        assert obj_id == 10
        mock_obj_repo.create.assert_called_once()
