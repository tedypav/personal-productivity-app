# Personal Productivity App — Project Plan

## Tech Stack
- **UI:** Python + PyQt6 (desktop & tablet-friendly)
- **Storage:** SQLite
- **Text Editing:** Rich text (HTML-based via QTextEdit)
- **Page Organization:** Sidebar tree / nested hierarchy

---

## MVP Scope

Core features for initial delivery:
- Page tree with nested hierarchy (CRUD, drag/reorder)
- Rich text editing with formatting toolbar
- Tables with row/column add/remove, row numbers, Tab navigation
- Checklists with checkbox toggle, add/remove items
- Text box widgets with multiple blocks (text, checklist, table, image)
- Floating widgets on free-form canvas with drag-and-drop positioning
- Resizable widgets with edge handles
- Template save and insert
- Auto-save and responsive layout (desktop + tablet)
- Bulk date-based page creation (days/weeks/years) with validation
- Bulk named page creation
- No-confirmation deletion with 15-minute undo (recursive page tree restoration)
- Multi-select sidebar with bulk delete
- Fun Imports (emoji & GIF picker)
- Global unhandled exception handler
- Keyboard shortcuts for all frequent actions

**Deferred until after MVP:**
- AI integration (OpenAI/Anthropic)
- Mobile phone optimization

---

## Modules

### Module 1: Core Architecture & Project Setup
- PyQt6 application scaffold with `QMainWindow`
- SQLite database initialization with schema migrations (WAL journal mode, foreign keys enforced)
- Schema migration via `ALTER TABLE ... ADD COLUMN` with try/except for incremental evolution
- Main layout: **Sidebar tree (left)** + **Page editor (right)**
- Config/settings file for user preferences (`settings.json`) with merge-over-defaults and corrupt-JSON fallback
- Responsive layout that adapts to tablet dimensions
- Persisted window geometry preferences
- Application-wide QSS stylesheet for consistent visual styling (`src/styles.py`)
- Global unhandled exception handler (`sys.excepthook`) showing `QMessageBox.critical` dialog
- Database connection closed on app exit via `aboutToQuit` signal

**Acceptance criteria:**
- App launches showing a split-pane layout
- Sidebar is collapsible
- Window resizes gracefully (test at 1024×768 and 1920×1080)
- Settings persist across restarts
- Unhandled exceptions show error dialog instead of silent crash
- Database uses WAL mode and enforces foreign keys

---

### Module 2: Page Management
- CRUD operations (create, rename, delete, reorder pages)
- **Nested hierarchy** via `parent_id` — context menu (Move Up/Down)
- **Multi-select** — Ctrl+click / Shift+click for batch operations (ExtendedSelection mode)
- **Bulk delete** — select multiple pages, right-click **Delete Selected (N)**, or `Ctrl+D` / `Delete` key
- **Undo delete** — all deletions (single/bulk) are stored for **15 minutes** and restored via **Edit → Undo Delete** (`Ctrl+Shift+Z`, `Ctrl+U`, or `Ctrl+Z` with sidebar focus); each press undoes one action, supporting multiple undos in sequence
- **Recursive page tree undo** — restoring a deleted page recursively restores all child pages and objects (preserving full hierarchy and original DB IDs)
- **New Page as child** — `Ctrl+N` / "+ New Page" creates children under ALL selected page(s); creates root-level page if none selected
- **Bulk time-based page creation** — dialog with three modes; end date dynamically adjusts when start changes (+1d / +7d / +1y); end date auto-validated with minimum ranges; "Week starts on" combo only visible in Weeks mode; date editors have calendar popups

  | Mode | Page Name | Logic |
  |------|-----------|-------|
  | **Days** | `YYYY-MM-DD` | User picks start & end date → one page per day |
  | **Weeks** | `YYYY-MM-DD - YYYY-MM-DD` | User picks a reference date + start-of-week day (Mon/Tue/.../Sun) → find nearest past start-of-week on or before ref date → generate N weekly pages forward from that start |
  | **Years** | `YYYY` | User picks start & end year → one page per year |

- **Bulk named page creation** — click "Name Pages" → enter base name (default: "Page") + count (default: 5, range: 1–999) → creates `BaseName 1`, `BaseName 2`, ...; empty name rejected
- **Expand/Collapse** — "Show All" / "Hide All" buttons in sidebar; manually collapsed branches persist across refreshes; tree uses 16px indentation and animated transitions
- **Context menu behavior** — multi-select shows only bulk actions (Delete Selected); single-page actions hidden
- **Page menu Delete redirect** — Page → Delete Current Page redirects to bulk delete when multiple pages selected
- **Archive** — right-click → "Archive" moves page to Archive folder; system folders cannot be archived
- **Set as Template** — right-click → "Set as Template" copies page to Templates folder with `template_page` type
- **Drag-and-drop reordering** — drag pages in sidebar tree; drop on folder to make child; folders cannot be nested under non-folder pages
- Pages stored in `pages` table (id, title, parent_id, sort_order, page_type, timestamps)
- `sort_order` auto-calculated as MAX(sort_order) + 1 for the given parent

**Acceptance criteria:**
- Pages can be created, renamed, deleted, and nested under parents
- Multiple pages can be selected and bulk-deleted (undos as single action)
- Undo restores any deletion within 15 minutes (recursively for page trees)
- Bulk creation generates correct page names per the format table
- Week calculation correctly snaps to the user-chosen start-of-week day
- Ctrl+N with selection creates child pages under ALL selected; with no selection creates root-level
- Show/Hide All buttons toggle tree; manual collapse state survives refresh
- Bulk create dialog validates end date ranges and shows/hides week-start combo per mode
- Context menu shows only bulk actions when multiple pages selected
- Drag-and-drop reordering works; folders cannot be nested under non-folder pages

---

### Module 3: Content Widgets — Text Box
- **Text box widgets** floating on a free-form canvas
- **Rich text editing** via QTextEdit (HTML-based) with formatting toolbar
- **Formatting toolbar** — Bold, Italic, H1, H2, Link, Bullet List, alignment (left/center/right), font size (9–32pt)
- **Multiple text blocks** — add/remove text blocks within a single text box
- **Sub-blocks** — inline checklist blocks, table blocks, image blocks within text boxes
- **Fun Imports** — emoji and GIF insertion via dialog
- **Editable title** — click to rename the text box
- **Drag-and-drop positioning** — drag header to move anywhere on canvas
- **Resize** — edge handles for width/height, corner handles for 2D resize
- **Position and size persistence** — stored in `page_objects` table as `textbox_meta` JSON
- Stored in `page_objects` table with `object_type='textbox_meta'` and `object_type='checkbox'` for inline checklists
- Auto-save on content change (debounced, default 1s interval; timer interval updates immediately on settings change)

**Acceptance criteria:**
- Text boxes persist rich text content and render formatted output
- Toolbar buttons apply correct formatting (bold, italic, headings, links, bullets)
- Text boxes can be freely dragged and positioned within canvas bounds
- Text boxes can be resized via edge and corner handles
- Multiple text blocks can be added/removed within a text box
- Inline checklist blocks, table blocks, and image blocks work within text boxes
- Text box positions and sizes survive app restart
- Font size combo applies to the correct element based on focus

---

### Module 4: Content Widgets — Tables & Checklists
- **Table widgets** floating on a free-form canvas
  - Dynamic rows/columns (+ Row / - Row / + Col / - Col)
  - Tab/Shift+Tab navigation between cells
  - Double-click column headers to rename inline
  - Row number toggle (#)
  - Drag-and-drop positioning and resize
  - Position and size persistence via `table_meta` JSON
- **Checklist widgets** floating on a free-form canvas
  - Custom-painted checkbox indicators (purple when checked)
  - Editable text per item
  - Add/remove items
  - Enter key creates new item
  - Drag-and-drop positioning and resize
  - Position and size persistence via `checklist_meta` JSON
- Both widget types use `ResizableMixin` for shared drag/resize logic
- Stored in `page_objects` table with `object_type='table_meta'` and `object_type='checklist_meta'` for containers, `object_type='checkbox'` for checklist items

**Acceptance criteria:**
- Tables can have rows/columns added and removed
- Tab/Shift+Tab navigates between cells; Tab at last cell auto-adds row
- Double-click column header enables inline rename
- Row numbers can be toggled on/off
- Checkboxes toggle visual state (custom purple checkmark)
- Checklist items can be individually added and deleted
- Both widget types can be dragged to any position on the canvas
- Both widget types can be resized via edge and corner handles
- Widget positions and sizes persist across sessions

---

### Module 5: Template System
- Save any page as a **template** via right-click → "Set as Template"
- Templates are copied to the Templates folder with `page_type='template_page'`
- **Insert template** — click "📋 Import Template" button in editor toolbar → select a template → objects copied to current page
- Template objects are copied via `PageObjectRepo.copy_objects()`
- Confirmation message on save: "Page {name} saved as a template."
- Info messages: "No templates saved yet." when inserting with no templates
- Templates displayed in the lower template tree section of the sidebar

**Acceptance criteria:**
- Saving a template copies all objects of the page to a new template_page
- Inserting a template copies its objects to the current page
- Templates survive app restart (persisted in SQLite)
- Confirmation and info messages shown at appropriate times

---

### Module 6: UI Polish & Data Persistence
- **Auto-save** on all content changes (timer-based, configurable interval; applied immediately on settings change)
- **Collapsible sidebar** via View → Toggle Sidebar
- **Resizable splitter** panels between sidebar and editor (stretch factor 1:3; initial sizes from `sidebar_width` setting)
- **Page title display** in editor toolbar (click-to-edit QLineEdit styled as label; "Select a page" when no page loaded; saves on Enter/focus lost, reverts on Escape/empty; sidebar renames sync to editor)
- **Keyboard shortcuts:**

  | Shortcut | Context | Action |
  |----------|---------|--------|
  | `Ctrl+N` | Global | New Page (as child if pages selected) |
  | `Ctrl+Shift+N` | Global | New Child Page |
  | `Ctrl+S` | Global | Save |
  | `Delete` | Sidebar | Delete page(s) — single or bulk |
  | `Ctrl+D` | Sidebar | Delete Selected (bulk) |
  | `Ctrl+Shift+Z` | Global | Undo Delete |
  | `Ctrl+U` | Global | Undo Delete |
  | `Ctrl+Z` | Sidebar focus only | Undo Delete |
  | `Ctrl+Shift+B` | Global | Bulk Create Pages |
  | `Ctrl+B` | Text block focused | Bold |
  | `Ctrl+I` | Text block focused | Italic |
  | `Ctrl+Q` | Global | Exit |
  | `Tab` | Table cell | Next cell |
  | `Shift+Tab` | Table cell | Previous cell |
  | `F2` | Sidebar focused | Rename selected page |

- **Settings dialog** (File → Settings): week start day, auto-save interval (500–10000ms, step 500), font size (10–32, requires restart); shows "Settings saved. Restart to apply font size changes." on save
- **Additional persisted settings** (not in dialog): `sidebar_width` (default: 250), `sidebar_splitter_sizes`, `main_splitter_sizes`, `theme` (default: "light")
- **Sidebar vertical splitter** — separates page tree (upper) from template tree (lower) with persisted sizes
- **Background image** — canvas shows photo background when no page is selected

**Acceptance criteria:**
- All keyboard shortcuts work and are discoverable
- Sidebar collapse/expand is smooth
- Auto-save interval change applies immediately
- Splitter sizes persist across sessions
- Background image displays correctly on empty canvas

---

## Architectural Choices

- **Data layer**: SQLite via `sqlite3` (stdlib) with a thin repository pattern (`page_repo.py`, `page_object_repo.py`)
- **Controller pattern**: Business logic separated into `src/controllers/` classes (PageController, EditorController, ChecklistController, TableController, TextboxController)
- **Content model**: Pages own an ordered list of page objects. Each object has a type (checkbox, checklist_meta, table_meta, textbox_meta) and a JSON content payload.
- **Floating widgets**: ChecklistWidget, TableWidget, TextboxWidget inherit from ResizableMixin for shared drag/resize logic. Each widget persists its position, size, and title as JSON metadata in the `page_objects` table.
- **Rich text**: Text box widgets use QTextEdit for HTML-based editing with formatting toolbar. No Markdown rendering.
- **Templates**: Page objects are copied from source to destination page via `PageObjectRepo.copy_objects()`. Template pages use `page_type='template_page'`.
- **Undo model**: In-memory `UndoManager` singleton stores deleted page trees with timestamps; auto-prunes entries older than 15 minutes. On undo, restores with original DB IDs. Page undo recursively restores full child hierarchy.
- **Focus tracking**: `PageEditor` connects to `QApplication.focusChanged` to track which widget has focus for context-aware formatting controls.
- **Widget serialization**: Text box blocks serialize as `[{"type": "text", "content": "<html>"}, ...]`. Table metadata includes headers, data, row numbers, position, and size. Checklist metadata includes position, size, and title.

---

## Database Schema

| Table | Key Columns |
|-------|-------------|
| `pages` | id (PK), title (DEFAULT 'Untitled'), parent_id (FK self, nullable, CASCADE), sort_order, page_type (DEFAULT 'page'), created_at, updated_at |
| `page_objects` | id (PK), page_id (FK, CASCADE), object_type (checkbox/checklist_meta/table_meta/textbox_meta), content (JSON), is_checked (bool), sort_order, created_at |

- All foreign keys use `ON DELETE CASCADE`
- `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON` on every connection
- `sqlite3.Row` row factory for dictionary-like access
- Schema migrations via `ALTER TABLE ... ADD COLUMN` with try/except
- Auto-calculated `sort_order` on create (MAX + 1 for given parent)

---

## Excluded Scope (Future)

### AI Integration
- Integrate OpenAI/Anthropic API via an `ai_service.py` module
- Bring-your-own-API-key in settings
- Potential features:
  - **AI write/rewrite** — select text and prompt "make this professional", "summarize", etc.
  - **Smart page generation** — natural language prompts like "Create a weekly planning page"
  - **Natural language commands** — "Create a page for each day this week"
  - **Semantic search** — search pages by meaning, not just keywords
  - **Task suggestions** — AI suggests priorities based on page content

### Mobile Optimization
- Phone-specific layout and touch gestures
- Native mobile build via PyQt6 for Android/iOS

---

## Workflow Rules

1. **All feature requests must be written in this project plan** before implementation.
2. **Test all features in the plan** before saving new changes — run through the checklist in `instructions`.
3. Update this plan when scope changes so it always reflects the current state of the application.
4. **Read the `instructions` file** before starting work to understand testing requirements for your feature type.
5. **Update the `instructions` file** when adding new features to maintain regression checklist and testing guides.

**For detailed development workflow, commands, and AI guidelines, see `DEVELOPMENT.md`.**
