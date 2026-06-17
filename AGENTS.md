# Personal Productivity App — Project Rules

## Project overview
A PyQt6 desktop app for organizing notes, tasks, and plans. Uses SQLite for persistence, free-form canvas for content widgets, and a hierarchical page tree.

## Architecture
- `src/ui/` — PyQt6 widgets (sidebar, editor, dialogs, canvas)
- `src/ui/objects/` — Reusable widget components (checklist, table, textbox, checkbox, resizable mixin)
- `src/controllers/` — Business logic (page, editor, checklist, table, textbox controllers)
- `src/repositories/` — Database CRUD operations (PageRepo, PageObjectRepo)
- `src/models/` — Dataclasses (Page, PageObject)
- `src/` — Core (database, settings, undo manager, styles, seed data)
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
- Controller pattern for business logic
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
