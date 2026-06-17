# Development Quick-Start

**For feature specifications and project scope, see `project_plan.md`.**
**For testing instructions and regression checklists, see `instructions`.**

## First Time Setup

```powershell
# Install all dependencies
py -m pip install -r requirements.txt
py -m pip install ruff mypy pre-commit pytest-cov

# Install pre-commit hooks
py -m pre_commit install
```

## Daily Workflow

### Starting Work
```powershell
# Ensure baseline passes
py -m pytest
```

### During Development (Hybrid Approach)

1. **Read `instructions` file** to understand testing requirements for your feature type
2. **Write unit tests first** for new functions/methods
3. **Implement minimally** to pass tests
4. **Add integration tests** for feature interactions
5. **Run tests after each change**:
   ```powershell
   py -m pytest tests/test_<affected>.py -v
   ```

### Before Committing
```powershell
# Run full test suite with coverage
py -m pytest --cov=src --cov-report=term-missing

# Check and fix code quality
py -m ruff check src/
py -m ruff check --fix src/
py -m ruff format src/

# Type check
py -m mypy src/

# Manual regression testing for affected features
# Follow the testing guides in `instructions` file

# Update `instructions` file if you added new features
# (add regression test steps, update feature specs, etc.)

# Pre-commit runs automatically on git commit
git commit -m "your message"
```

### Before Merging to Main

1. **Sync documentation** — Ask the docs agent to update documentation:
   ```
   @docs sync documentation with current implementation
   ```
2. **Run full test suite** — Ensure all tests pass:
   ```powershell
   py -m pytest --cov=src --cov-report=term-missing
   ```
3. **Check code quality** — Ensure ruff and mypy pass:
   ```powershell
   py -m ruff check src/
   py -m mypy src/
   ```
4. **Manual regression** — Run affected steps from the `instructions` checklist

## Debugging workflow

When the user reports a bug, follow this process strictly:

1. **REPRODUCE** — Run the app or a test that demonstrates the bug. Never guess at a fix without seeing the problem first.
2. **UNDERSTAND** — Read the relevant source files and trace the execution path. Explain your understanding of the bug back to the user before writing any code.
3. **PLAN** — Describe what you think the fix should be. Get confirmation before implementing.
4. **ONE CHANGE** — Make exactly one small, targeted change.
5. **VERIFY** — Run the affected tests immediately after that one change.
6. **REPEAT** — If not fixed, go back to step 2. Do not make multiple unrelated changes hoping something sticks.

### Rules for debugging:
- NEVER make more than one change before testing
- NEVER skip running tests after a change
- NEVER guess at a fix — understand the root cause first
- If a fix doesn't work after 2 attempts, STOP and explain what you tried to the user
- ALWAYS run `py -m pytest` before starting (confirm baseline)
- ALWAYS run `py -m pytest` after each individual change

## Using the Instructions File

The `instructions` file is your comprehensive testing guide. Use it to:

1. **Understand feature requirements** - each feature has detailed specs
2. **Follow regression checklists** - 90-step quick regression checklist
3. **Use feature-specific testing guides** - targeted tests for different feature types
4. **Prioritize testing** - high/medium/low priority sections

### Feature-Specific Testing

When implementing a feature, look up its type in the `instructions` file:

- **Adding New UI Components** → See "Feature-Specific Testing Guides" section
- **Adding New Database Operations** → See "Feature-Specific Testing Guides" section
- **Adding New Keyboard Shortcuts** → See "Feature-Specific Testing Guides" section
- **Adding New Context Menu Items** → See "Feature-Specific Testing Guides" section
- **Adding New Formatting Features** → See "Feature-Specific Testing Guides" section
- **Adding New Canvas/Widget Features** → See "Feature-Specific Testing Guides" section
- **Adding New Checklist Features** → See "Feature-Specific Testing Guides" section
- **Adding New Template Features** → See "Feature-Specific Testing Guides" section
- **Adding New Settings Features** → See "Feature-Specific Testing Guides" section

### Regression Testing Priority

When time is limited, prioritize based on what was changed:

- **High Priority (Always Run)**: Steps 1-2, 5, 32
- **Medium Priority (Run if UI Changed)**: Steps 14-17, 33-53
- **Low Priority (Run if Specific Feature Changed)**: Steps 59-70, 71-74, 79-80

## Common Issues

### Tests fail after changes
1. Check what changed: `git diff`
2. Run specific test: `py -m pytest tests/test_<file>.py -v`
3. Check error message and fix
4. Follow regression checklist in `instructions` for affected features

### Coverage drops below 90%
1. Run: `py -m pytest --cov=src --cov-report=term-missing`
2. Add tests for uncovered lines
3. Re-run to verify

### Ruff/Mypy errors
1. Auto-fix: `py -m ruff check --fix src/`
2. Manual fix remaining issues
3. Re-run checks

### Pre-commit hooks fail
1. Fix the issues reported
2. Stage changes: `git add .`
3. Try commit again

## Quality Tools

- **Ruff**: Linting and formatting
- **Mypy**: Type checking
- **Pytest**: Testing with coverage
- **Pre-commit**: Automated quality gates
- **Instructions**: Manual testing and regression checklists

## Quick Reference

```powershell
# Run all tests
py -m pytest

# Run specific test file
py -m pytest tests/test_models.py -v

# Run tests with coverage
py -m pytest --cov=src --cov-report=term-missing

# Check code quality
py -m ruff check src/
py -m mypy src/

# Auto-fix and format
py -m ruff check --fix src/
py -m ruff format src/

# Run pre-commit on all files
py -m pre_commit run --all-files
```

---

## AI Assistant Guidelines

This section provides specific rules and conventions for AI assistants working on this codebase.

### Project Structure

```
personal-productivity-app/
├── run.py                          # Entry point
├── src/
│   ├── main.py                     # App bootstrap, QSS, fonts, exception handler
│   ├── database.py                 # SQLite connection + schema migrations
│   ├── settings.py                 # JSON settings load/save
│   ├── undo_manager.py             # Undo/restore for deletions
│   ├── styles.py                   # Application-wide QSS stylesheet
│   ├── seed_data.py                # Fun pre-populated pages
│   ├── models/                     # Dataclasses (Page, PageObject)
│   ├── repositories/               # CRUD operations (PageRepo, PageObjectRepo)
│   ├── controllers/                # Business logic (PageController, EditorController,
│   │                               #   ChecklistController, TableController, TextboxController)
│   └── ui/                         # PyQt6 widgets (main_window, sidebar, editor)
│       └── objects/                # Reusable widget components
├── tests/                          # pytest + pytest-qt tests
├── assets/                         # Fonts, icons, design tokens
├── instructions                    # Testing instructions and regression checklists
├── project_plan.md                 # Feature specifications and workflow rules
├── TODO.md                         # Outstanding issues and tech debt
└── DEVELOPMENT.md                  # This file
```

### Architecture Patterns

- **Repository pattern**: All database access goes through `src/repositories/` classes (PageRepo, PageObjectRepo)
- **Controller pattern**: Business logic separated into `src/controllers/` classes (PageController, EditorController, ChecklistController, TableController, TextboxController)
- **Dataclass models**: Domain objects in `src/models/` are simple dataclasses (Page, PageObject)
- **SQLite with WAL mode**: Database uses `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON`
- **Schema migrations**: Use `ALTER TABLE ... ADD COLUMN` with try/except for incremental evolution
- **Undo manager**: 15-minute TTL with recursive page tree restoration
- **ResizableMixin**: Shared drag/resize logic for floating widgets (ChecklistWidget, TableWidget, TextboxWidget)

### Database Schema

| Table | Key Columns |
|-------|-------------|
| `pages` | id (PK), title (DEFAULT 'Untitled'), parent_id (FK self, nullable, CASCADE), sort_order, page_type (DEFAULT 'page'), created_at, updated_at |
| `page_objects` | id (PK), page_id (FK, CASCADE), object_type (checkbox/checklist_meta/table_meta/textbox_meta), content (JSON), is_checked (bool), sort_order, created_at |

- All foreign keys use `ON DELETE CASCADE`
- `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON` on every connection
- `sqlite3.Row` row factory for dictionary-like access
- Schema migrations via `ALTER TABLE ... ADD COLUMN` with try/except
- Auto-calculated `sort_order` on create (MAX + 1 for given parent)

### Code Conventions

- **Python 3.10+**: Use modern syntax (type hints, match statements, etc.)
- **Double quotes**: Use double quotes for strings (enforced by ruff)
- **88-char line length**: Maximum line length (enforced by ruff)
- **Import order**: stdlib → third-party → local (enforced by ruff isort)

### Things to Avoid

1. **Never modify `app.db` directly** - always use repository classes
2. **Never skip tests** - maintain 90% coverage minimum
3. **Never commit without running quality checks** - ruff, mypy, pytest
4. **Never ignore the instructions file** - it contains critical regression checklists
5. **Never assume library availability** - check existing dependencies first
6. **Never add comments unless asked** - keep code clean
7. **Never commit secrets or keys** - check `.gitignore` patterns

### Preferred Patterns

**Adding a new repository:**
```python
# src/repositories/new_repo.py
from src.database import get_connection
from src.models.new_model import NewModel

class NewRepo:
    def create(self, item: NewModel) -> int:
        conn = get_connection()
        # ... implementation
        return item.id
```

**Adding a new controller:**
```python
# src/controllers/new_controller.py
from PyQt6.QtCore import QObject, pyqtSignal

class NewController(QObject):
    data_changed = pyqtSignal()

    def __init__(self, repo=None):
        super().__init__()
        self._repo = repo or NewRepo()
```

**Adding a new test file:**
```python
# tests/test_new_feature.py
import pytest
from src.new_module import NewClass

def test_new_function():
    # Arrange
    # Act
    # Assert
    pass
```

**Adding a new UI widget:**
- Inherit from appropriate Qt widget and ResizableMixin if floating
- Use existing QSS styles from `src/styles.py`
- Follow existing patterns in `src/ui/objects/`

### Common Gotchas

1. **Qt signal connections**: Always connect signals in `__init__`, not in methods
2. **Database connections**: Use `get_connection()` context manager for automatic cleanup
3. **Thread safety**: Qt widgets must only be modified from the main thread
4. **Memory management**: Qt handles most cleanup, but watch for circular references
5. **File paths**: Use `os.path.join()` for cross-platform compatibility
6. **Database close on exit**: `main.py` connects `aboutToQuit` to `close_connection()`
7. **Undo manager**: `_restore()` does NOT close the global connection (allows continued use)

### Testing Guidelines

- **Unit tests**: Test individual functions/methods in isolation
- **Integration tests**: Test how components work together
- **UI tests**: Use `pytest-qt` for widget testing
- **Fixtures**: Use existing fixtures in `conftest.py` (temp_db, qapp, repos)
- **Coverage**: Aim for 90%+ coverage, focus on critical paths

### When Adding New Features

1. **Read `instructions` file** for feature-specific testing guides
2. **Check `project_plan.md`** for existing specifications
3. **Write tests first** (TDD approach recommended)
4. **Follow repository pattern** for any new database operations
5. **Follow controller pattern** for any new business logic
6. **Update documentation** (instructions, project_plan.md, this file if needed)
7. **Run full regression** before committing

### When Fixing Bugs

1. **Write a test that reproduces the bug** first
2. **Fix the bug** until the test passes
3. **Run full regression** to ensure no side effects
4. **Update `instructions` file** if the bug reveals a gap in testing

### Performance Considerations

- **Database queries**: Use indexes, avoid N+1 queries
- **Qt widgets**: Minimize widget creation in loops
- **Auto-save**: Default 1000ms interval, configurable 500-10000ms
- **Large datasets**: Consider pagination for page lists
