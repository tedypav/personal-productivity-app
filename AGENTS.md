# Personal Productivity App — Project Rules

## Project overview
A PyQt6 desktop app for organizing notes, tasks, and plans. Uses SQLite for persistence, free-form canvas for content blocks, and a hierarchical page tree.

## Architecture
- `src/ui/` — PyQt6 widgets (sidebar, editor, dialogs, canvas)
- `src/ui/objects/` — Reusable widget components (checklist, table, checkbox, resizable mixin)
- `src/repositories/` — Database CRUD operations
- `src/models/` — Dataclasses (Page, PageObject)
- `src/` — Core (database, settings, undo manager, styles)
- `tests/` — pytest + pytest-qt tests
- `scripts/` — Pre-commit check scripts

## Files to reference contextually

### `DEVELOPMENT.md`
- **Read when:** running tests, checking code quality, committing, starting a new feature
- Contains: workflow commands, quality tool config, AI assistant guidelines

### `instructions`
- **Read when:** writing tests, adding features, running regression checks
- Contains: 90-step regression checklist, feature-specific testing guides

### `project_plan.md`
- **Read when:** implementing new features, checking what's already built
- Contains: feature specs, acceptance criteria, architectural decisions

## Code conventions
- Python 3.10+, double quotes, 88-char lines
- Repository pattern for database access
- Dataclass models in `src/models/`
- SQLite with WAL mode and foreign keys
- 90% test coverage minimum

## Before any code change
1. Check `instructions` for affected test scenarios
2. Run `py -m pytest --cov=src --cov-report=term-missing`
3. Run `py -m ruff check src/` and `py -m mypy src/`

## Before merging
1. Run `@docs sync documentation with current implementation`
2. Run full test suite
3. Check ruff and mypy pass
