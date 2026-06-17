import json
from unittest.mock import MagicMock

import pytest

from src.controllers.table_controller import TableController


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def controller(mock_repo):
    return TableController(page_object_repo=mock_repo)


class TestTableController:
    def test_save_meta_creates_new(self, controller, mock_repo):
        mock_repo.get_table_meta.return_value = None
        mock_repo.create.return_value = 1
        data = [["A", "B"], ["C", "D"]]
        controller.save_meta(1, 1, 10, 20, 300, 200, 2, 2, data, False)
        mock_repo.create.assert_called_once()
        call_args = mock_repo.create.call_args[0][0]
        assert call_args.object_type == "table_meta"
        content = json.loads(call_args.content)
        assert content["rows"] == 2
        assert content["data"] == data

    def test_save_meta_updates_existing(self, controller, mock_repo):
        mock_meta = MagicMock()
        mock_repo.get_table_meta.return_value = mock_meta
        data = [["X", "Y"]]
        controller.save_meta(1, 1, 30, 40, 400, 300, 1, 2, data, True)
        mock_repo.update.assert_called_once_with(mock_meta)
        content = json.loads(mock_meta.content)
        assert content["has_header"] is True

    def test_load_meta_returns_data(self, controller, mock_repo):
        mock_meta = MagicMock()
        data = {"x": 10, "y": 20, "rows": 3}
        mock_meta.content = json.dumps(data)
        mock_repo.get_table_meta.return_value = mock_meta
        result = controller.load_meta(1, 1)
        assert result is not None
        assert result["rows"] == 3

    def test_load_meta_returns_none_when_not_found(self, controller, mock_repo):
        mock_repo.get_table_meta.return_value = None
        result = controller.load_meta(1, 999)
        assert result is None

    def test_load_meta_handles_invalid_json(self, controller, mock_repo):
        mock_meta = MagicMock()
        mock_meta.content = "not json"
        mock_repo.get_table_meta.return_value = mock_meta
        result = controller.load_meta(1, 1)
        assert result is None

    def test_delete_meta(self, controller, mock_repo):
        controller.delete_meta(1)
        mock_repo.delete.assert_called_once_with(1)

    def test_update_cell(self, controller, mock_repo):
        mock_meta = MagicMock()
        data = {"data": [["A", "B"], ["C", "D"]]}
        mock_meta.content = json.dumps(data)
        mock_repo.get_table_meta.return_value = mock_meta
        controller.update_cell(1, 1, 0, 1, "X")
        content = json.loads(mock_meta.content)
        assert content["data"][0][1] == "X"
        mock_repo.update.assert_called_once_with(mock_meta)

    def test_update_cell_no_meta(self, controller, mock_repo):
        mock_repo.get_table_meta.return_value = None
        controller.update_cell(1, 999, 0, 0, "X")
        mock_repo.update.assert_not_called()

    def test_update_cell_emits_signal(self, controller, mock_repo):
        mock_meta = MagicMock()
        data = {"data": [["A"]]}
        mock_meta.content = json.dumps(data)
        mock_repo.get_table_meta.return_value = mock_meta
        emitted = []
        controller.cell_changed.connect(
            lambda r, c, t, ct: emitted.append((r, c, t, ct))
        )
        controller.update_cell(1, 1, 0, 0, "Z")
        assert (0, 0, 1, "Z") in emitted
