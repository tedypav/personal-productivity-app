<p align="center">
  <img src="assets/icons/logo_icon.svg" width="80" alt="App logo">
</p>

<h1 align="center">Personal Productivity App</h1>

<p align="center">
  A desktop productivity app with a freeform canvas editor, built with PyQt6 and SQLite.<br>
  Organize pages, checklists, tables, and rich text — all on a drag-and-drop canvas.
</p>

<p align="center">
  <img src="assets/screenshots/01_welcome.png" width="100%" alt="Welcome screen with sidebar and page tree">
</p>

---

## Features

### Page & Folder Management
- Hierarchical page tree with folders and nested pages
- Bulk create pages by date range (days, weeks, years) or numbered sequences
- Archive pages to a dedicated Archive folder
- Move pages between folders via dialog
- Multi-select with Shift/Ctrl for bulk operations
- Context menu: rename, delete, archive, move, reorder
- Drag-and-drop reordering with parent folder targeting

### Free-Form Canvas Editor
- Three floating widget types: **Checklist**, **Table**, **Text Box**
- Freeform positioning — drag widgets anywhere on the canvas
- Resizable widgets with edge handles (left, right, top, bottom, corners)
- Draggable headers for repositioning
- Infinite vertical scroll canvas with background image

### Rich Text Editing (Text Box Widget)
- Rich text editing via QTextEdit (HTML-based)
- Formatting toolbar: Bold, Italic, H1, H2, Link, Bullet List
- Font size selector (9–32pt)
- Text alignment (left, center, right)
- Inline image blocks (from file or URL)
- GIF and emoji insertion via Fun Imports dialog

### Checklists
- Custom-painted checkbox indicators with toggle state
- Editable text per item
- Add/remove items
- Resizable checklist containers with drag-and-drop positioning
- Metadata persistence (position, size, title)

### Tables
- Dynamic add/remove rows and columns
- Tab/Shift+Tab navigation between cells
- Double-click column headers to rename
- Row number toggle
- Resizable table containers with drag-and-drop positioning

### Emoji & GIF Support
- Categorized emoji picker (Smileys, Gestures, Hearts, Animals, Food, Activities, Travel, Objects)
- GIF browser with categories (Trending, Reactions, Celebrations)
- Custom emoji and GIF upload support
- Insert at cursor position in any text field

### Undo System
- Undo page deletions with Ctrl+Z / Ctrl+Shift+Z / Ctrl+U
- 15-minute TTL — actions expire after 15 minutes
- Recursive restore for full page trees (page + children + objects)

### Auto-Save & Settings
- Configurable auto-save interval (500–10,000ms)
- Customizable font size, week start day, and theme
- Settings stored in `settings.json`
- Splitter sizes persisted across sessions

### Seed Data
- Fun pre-populated "World Domination Plan" page with checklists, tables, and rich text

---

## Tech Stack

| Component | Detail |
|-----------|--------|
| Language | Python 3.10+ |
| GUI | [PyQt6](https://pypi.org/project/PyQt6/) >= 6.11 |
| Rich Text | Qt QTextEdit (HTML-based) |
| Database | SQLite3 (WAL mode, foreign keys) |
| Testing | pytest, pytest-qt, pytest-cov |
| Linting | [ruff](https://github.com/astral-sh/ruff) |
| Type checking | [mypy](https://mypy-lang.org/) |

---

## Getting Started

### Prerequisites

- Python 3.10 or later
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/tedypav/personal-productivity-app.git
cd personal-productivity-app

# Install dependencies
pip install -r requirements.txt

# Install development tools (optional)
pip install ruff mypy pre-commit pytest-cov pytest-qt

# Install pre-commit hooks (optional)
pre-commit install
```

### Running the App

```bash
python run.py
```

The app opens maximized. The database (`app.db`) and settings (`settings.json`) are created automatically on first run.

---

## Project Structure

```
personal-productivity-app/
├── run.py                          # Entry point
├── pyproject.toml                  # Project config and tool settings
├── requirements.txt                # Runtime dependencies
├── TODO.md                         # Outstanding issues and tech debt
├── assets/
│   ├── background/                 # Welcome screen background
│   ├── fonts/                      # Inter, Playfair Display, Magnolia
│   ├── icons/                      # App icons (SVG, ICO)
│   ├── mockups/                    # Design mockups
│   ├── screenshots/                # App screenshots for README
│   └── ui/                         # Design tokens (colors, spacing)
├── src/
│   ├── main.py                     # App bootstrap, stylesheet, fonts, exception handler
│   ├── database.py                 # SQLite connection, schema, migrations
│   ├── settings.py                 # JSON settings load/save
│   ├── undo_manager.py             # Undo system with 15-min TTL
│   ├── styles.py                   # Application-wide QSS stylesheet
│   ├── seed_data.py                # Fun pre-populated pages
│   ├── models/                     # Dataclasses: Page, PageObject
│   ├── repositories/               # CRUD: PageRepo, PageObjectRepo
│   ├── controllers/                # Business logic: PageController, EditorController,
│   │                               #   ChecklistController, TableController, TextboxController
│   └── ui/
│       ├── main_window.py          # Main window, menu bar, shortcuts
│       ├── sidebar.py              # Page tree, templates, Fun Imports
│       ├── editor.py               # Canvas, floating widgets, editor components
│       ├── bulk_create_dialog.py   # Bulk page creation dialog
│       ├── dialogs.py              # Shared dialog utilities
│       ├── fun_imports.py          # Emoji and GIF picker dialog
│       └── objects/                # Reusable widget components
│           ├── checklist_widget.py # Floating checklist with checkboxes
│           ├── checkbox_widget.py  # Custom-painted checkbox indicator
│           ├── table_widget.py     # Floating table with editable cells
│           ├── textbox_widget.py   # Floating text box with rich text, images, checklists, tables
│           └── resizable_mixin.py  # Shared drag/resize logic for floating widgets
├── tests/                          # pytest + pytest-qt tests
│   ├── conftest.py                 # Shared fixtures (temp_db, mock dialogs)
│   ├── test_controllers/           # Controller unit tests
│   └── test_*.py                   # Feature-specific tests
└── scripts/                        # Pre-commit check scripts
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New page |
| `Ctrl+Shift+N` | New child page |
| `Ctrl+S` | Save |
| `Ctrl+Q` | Exit |
| `Ctrl+Z` | Undo delete (sidebar focus) |
| `Ctrl+Shift+Z` | Undo delete (global) |
| `Ctrl+U` | Undo delete (global) |
| `Ctrl+D` | Delete selected (sidebar or editor) |
| `Ctrl+Shift+B` | Bulk create pages |
| `Delete` | Delete selected page/widget |
| `F2` | Rename selected page |
| `Tab` | Next table cell |
| `Shift+Tab` | Previous table cell |

---

## Testing

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run a specific test file
python -m pytest tests/test_models.py -v

# Run with coverage report
python -m pytest --cov=src --cov-report=term-missing
```

Coverage target: 90% (enforced via `pyproject.toml`).

---

## Development

### Code Quality

```bash
# Lint
ruff check src/

# Format
ruff format src/

# Type check
mypy src/
```

### Pre-commit Hooks

The project uses pre-commit to enforce code quality on every commit:

- **ruff** — linting and auto-fix
- **ruff-format** — code formatting
- **mypy** — type checking
- **docs-sync-check** — verifies documentation is up to date
- **code-health-check** — verifies code health metrics

```bash
# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

---

## Acknowledgements

- **Inter** — UI body font
- **Playfair Display** — heading font
- **Magnolia** — decorative greeting font
- Design system based on warm pastel palette with soft shadows and rounded corners
