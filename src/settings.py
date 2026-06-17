"""JSON-based user settings persistence with merge-over-defaults loading."""

import json
import os

SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "settings.json"
)

DEFAULT_SETTINGS: dict = {
    "week_start_day": "Monday",
    "auto_save_interval_ms": 1000,
    "sidebar_width": 250,
    "sidebar_splitter_sizes": None,
    "main_splitter_sizes": None,
    "font_size": 14,
    "theme": "light",
}


def load_settings() -> dict:
    """Load settings from JSON file, merging over defaults.

    Creates the file with defaults if it doesn't exist. Falls back to
    defaults silently on corrupt JSON or I/O errors.
    """
    if not os.path.exists(SETTINGS_PATH):
        save_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
            merged = dict(DEFAULT_SETTINGS)
            merged.update(data)
            return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> None:
    """Persist the settings dict to JSON file."""
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
