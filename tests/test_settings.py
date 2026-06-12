import json
import os

from src.settings import DEFAULT_SETTINGS, SETTINGS_PATH, load_settings, save_settings


class TestLoadSettings:
    def test_returns_defaults_when_missing(self, monkeypatch, tmp_path):
        fake_path = str(tmp_path / "settings.json")
        monkeypatch.setattr("src.settings.SETTINGS_PATH", fake_path)
        result = load_settings()
        assert result == DEFAULT_SETTINGS
        assert os.path.exists(fake_path)

    def test_creates_file_when_missing(self, monkeypatch, tmp_path):
        fake_path = str(tmp_path / "settings.json")
        monkeypatch.setattr("src.settings.SETTINGS_PATH", fake_path)
        load_settings()
        assert os.path.exists(fake_path)
        with open(fake_path) as f:
            data = json.load(f)
        assert data == DEFAULT_SETTINGS

    def test_returns_defaults_on_corrupt_json(self, monkeypatch, tmp_path):
        fake_path = str(tmp_path / "settings.json")
        monkeypatch.setattr("src.settings.SETTINGS_PATH", fake_path)
        with open(fake_path, "w") as f:
            f.write("{invalid json")
        result = load_settings()
        assert result == DEFAULT_SETTINGS

    def test_merges_with_defaults(self, monkeypatch, tmp_path):
        fake_path = str(tmp_path / "settings.json")
        monkeypatch.setattr("src.settings.SETTINGS_PATH", fake_path)
        with open(fake_path, "w") as f:
            json.dump({"week_start_day": "Sunday"}, f)
        result = load_settings()
        assert result["week_start_day"] == "Sunday"
        auto_save = DEFAULT_SETTINGS["auto_save_interval_ms"]
        assert result["auto_save_interval_ms"] == auto_save
        assert result["sidebar_width"] == DEFAULT_SETTINGS["sidebar_width"]
        assert result["font_size"] == DEFAULT_SETTINGS["font_size"]
        assert result["theme"] == DEFAULT_SETTINGS["theme"]

    def test_full_settings_file(self, monkeypatch, tmp_path):
        fake_path = str(tmp_path / "settings.json")
        monkeypatch.setattr("src.settings.SETTINGS_PATH", fake_path)
        custom = {
            "week_start_day": "Friday",
            "auto_save_interval_ms": 2000,
            "sidebar_width": 300,
            "font_size": 18,
            "theme": "dark",
        }
        with open(fake_path, "w") as f:
            json.dump(custom, f)
        result = load_settings()
        for k, v in custom.items():
            assert result[k] == v

    def test_settings_path_resolves(self):
        assert "settings.json" in SETTINGS_PATH

    def test_corrupt_json_does_not_raise(self, monkeypatch, tmp_path):
        fake_path = str(tmp_path / "settings.json")
        monkeypatch.setattr("src.settings.SETTINGS_PATH", fake_path)
        with open(fake_path, "w") as f:
            f.write("not json at all {{{")
        result = load_settings()
        assert isinstance(result, dict)

    def test_multiple_load_save_cycles(self, monkeypatch, tmp_path):
        fake_path = str(tmp_path / "settings.json")
        monkeypatch.setattr("src.settings.SETTINGS_PATH", fake_path)
        settings = dict(DEFAULT_SETTINGS)
        for i in range(5):
            settings["auto_save_interval_ms"] = 500 + i * 500
            save_settings(settings)
            loaded = load_settings()
            assert loaded["auto_save_interval_ms"] == 500 + i * 500

    def test_new_default_keys_appear(self, monkeypatch, tmp_path):
        fake_path = str(tmp_path / "settings.json")
        monkeypatch.setattr("src.settings.SETTINGS_PATH", fake_path)
        with open(fake_path, "w") as f:
            json.dump({"week_start_day": "Tuesday"}, f)
        result = load_settings()
        assert "week_start_day" in result
        assert "auto_save_interval_ms" in result

    def test_splitter_size_defaults_are_none(self, monkeypatch, tmp_path):
        fake_path = str(tmp_path / "settings.json")
        monkeypatch.setattr("src.settings.SETTINGS_PATH", fake_path)
        result = load_settings()
        assert result["sidebar_splitter_sizes"] is None
        assert result["main_splitter_sizes"] is None

    def test_splitter_sizes_persist(self, monkeypatch, tmp_path):
        fake_path = str(tmp_path / "settings.json")
        monkeypatch.setattr("src.settings.SETTINGS_PATH", fake_path)
        settings = dict(DEFAULT_SETTINGS)
        settings["sidebar_splitter_sizes"] = [400, 200]
        settings["main_splitter_sizes"] = [300, 900]
        save_settings(settings)
        loaded = load_settings()
        assert loaded["sidebar_splitter_sizes"] == [400, 200]
        assert loaded["main_splitter_sizes"] == [300, 900]


class TestSaveSettings:
    def test_writes_valid_json(self, monkeypatch, tmp_path):
        fake_path = str(tmp_path / "settings.json")
        monkeypatch.setattr("src.settings.SETTINGS_PATH", fake_path)
        save_settings(DEFAULT_SETTINGS)
        with open(fake_path) as f:
            data = json.load(f)
        assert data == DEFAULT_SETTINGS

    def test_round_trip(self, monkeypatch, tmp_path):
        fake_path = str(tmp_path / "settings.json")
        monkeypatch.setattr("src.settings.SETTINGS_PATH", fake_path)
        custom = {
            "week_start_day": "Sunday",
            "auto_save_interval_ms": 2000,
            "sidebar_width": 300,
            "font_size": 18,
            "theme": "dark",
        }
        save_settings(custom)
        loaded = load_settings()
        for k, v in custom.items():
            assert loaded[k] == v
