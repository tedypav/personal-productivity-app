# TODO — Outstanding Issues

## Medium Severity (Tech Debt)

### #8: Duplication — `_save_meta` / `_load_meta` across widgets
- **Files**: `checklist_widget.py`, `table_widget.py`, `textbox_widget.py`
- **Issue**: All three widget types implement nearly identical `_save_meta` and `_load_meta` methods (sort_order encoding, JSON serialization, create-or-update pattern).
- **Fix**: Extract a `MetaWidgetMixin` or consolidate into existing controllers (ChecklistController, TableController, TextboxController).

### #9: Duplication — Drag/resize `eventFilter` logic
- **Files**: `checklist_widget.py`, `table_widget.py`, `textbox_widget.py`
- **Issue**: Although `ResizableMixin` exists, all three widgets duplicate ~80 lines of edge-detection, drag-start, resize-calculation, and boundary-clamping in their `eventFilter` methods.
- **Fix**: Either use the mixin's event methods consistently or consolidate the eventFilter logic into the mixin.

### #11: Oversized file — `editor.py` (715 lines)
- **Issue**: `PageEditor` has too many responsibilities: toolbar, page loading, object grouping, checklist/table/textbox creation, template import, TOC display, keyboard handling.
- **Fix**: Extract toolbar building and object management into separate modules or `EditorController`.

### #12: Oversized file — `sidebar.py` (1111 lines)
- **Issue**: Handles page CRUD, context menus, archive, templates, bulk creation, move-to-folder, tree expansion.
- **Fix**: Extract archive logic, bulk creation, and context menu handling into separate classes.

### #13: Oversized file — `textbox_widget.py` (1044 lines)
- **Issue**: Contains 5 classes (TextboxTextBlock, TextboxChecklistItem, TextboxChecklistBlock, TextboxTableBlock, TextboxImageBlock, TextboxWidget).
- **Fix**: Split into separate files: `text_block.py`, `checklist_block.py`, `table_block.py`, `image_block.py`.

### #14: Oversized file — `fun_imports.py` (895 lines)
- **Issue**: `EMOJI_DATA` is ~380 lines of hardcoded emoji. Dialog class is ~500 lines.
- **Fix**: Move `EMOJI_DATA` to `data/emoji_data.py`. Split upload/refresh logic from display logic.

## Low Severity

### #15: SQL injection surface in `_add_column`
- **File**: `database.py:37,39`
- **Issue**: Uses f-strings for SQL (`PRAGMA table_info({table})`, `ALTER TABLE {table} ADD COLUMN`). Internal-only code, low risk.
- **Fix**: Add a comment documenting why f-strings are used, or whitelist table names.

### #20: `_check_same_thread=False` without thread safety
- **File**: `database.py:17`
- **Issue**: Disables thread-safety check but no locks/mutexes are used. Currently single-threaded, but latent risk.
- **Fix**: Already has a comment. Consider adding a threading lock if multi-threading is ever needed.

### #21: Missing test files
- **Modules**: `resizable_mixin.py` (163 lines), `seed_data.py` (187 lines)
- **Issue**: Complex logic with no dedicated test files.
- **Fix**: Add tests for edge detection, boundary clamping, and seed data integration.

### #22: Repeated lazy imports in `main_window.py`
- **File**: `main_window.py:175,194`
- **Issue**: `from src.repositories.page_repo import PageRepo` repeated inside two methods.
- **Fix**: Move to top-level import (already done in `editor.py`).
