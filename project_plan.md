# Personal Productivity App — Project Plan

## Tech Stack
- **UI:** Python + PyQt6 (desktop & tablet-friendly)
- **Storage:** SQLite
- **Text Editing:** Markdown-based
- **Page Organization:** Sidebar tree / nested hierarchy

---

## MVP Scope

Core features for initial delivery:
- Page tree with nested hierarchy (CRUD, drag/reorder)
- Markdown content editing with formatting toolbar
- Tables with header row toggle, row numbers, multi-cell selection, Tab navigation, and embedded task lists
- Lists, checkboxes, recurring tasks (daily/weekly/monthly)
- Embedded task lists in text blocks and table cells
- Editable block headers with alignment (H/V), font size, and height resize
- Block multi-select on canvas with bulk delete
- Font size combo box in toolbar (context-aware per focused element)
- Template save and insert (with confirmation messages)
- Auto-save and responsive layout (desktop + tablet)
- Bulk date-based page creation (days/weeks/years) with validation
- Bulk named page creation
- No-confirmation deletion with 15-minute undo (recursive page tree restoration)
- Multi-select sidebar with bulk delete & bulk template insert
- Context-aware "+ List" button (adds to text block, table cell, or creates new block)
- Free-form canvas with click-to-place block positioning and auto-grid layout
- Block auto-fit to content with manual resize override
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
- Application-wide QSS stylesheet for consistent visual styling
- Global unhandled exception handler (`sys.excepthook`) showing `QMessageBox.critical` dialog

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
- **Undo delete** — all deletions (single/bulk, page/block/task) are stored for **15 minutes** and restored via **Edit → Undo Delete** (`Ctrl+Shift+Z`, `Ctrl+U`, or `Ctrl+Z` with sidebar focus); each press undoes one action, supporting multiple undos in sequence
- **Recursive page tree undo** — restoring a deleted page recursively restores all child pages, content blocks, and tasks (preserving full hierarchy and original DB IDs)
- **New Page as child** — `Ctrl+N` / "+ New Page" creates children under ALL selected page(s); creates root-level page if none selected
- **Bulk time-based page creation** — dialog with three modes; end date dynamically adjusts when start changes (+1d / +7d / +1y); end date auto-validated with minimum ranges; "Week starts on" combo only visible in Weeks mode; date editors have calendar popups

  | Mode | Page Name | Logic |
  |------|-----------|-------|
  | **Days** | `YYYY-MM-DD` | User picks start & end date → one page per day |
  | **Weeks** | `YYYY-MM-DD - YYYY-MM-DD` | User picks a reference date + start-of-week day (Mon/Tue/.../Sun) → find nearest past start-of-week on or before ref date → generate N weekly pages forward from that start |
  | **Years** | `YYYY` | User picks start & end year → one page per year |

- **Bulk named page creation** — click "+ Bulk Named" → enter base name (default: "Page") + count (default: 5, range: 1–999) → creates `BaseName 1`, `BaseName 2`, ...; empty name rejected
- **Expand/Collapse** — "Show All" / "Hide All" buttons in sidebar; manually collapsed branches persist across refreshes; tree uses 16px indentation and animated transitions
- **Context menu behavior** — multi-select shows only bulk actions (Delete Selected, Insert Template); single-page actions hidden
- **Page menu Delete redirect** — Page → Delete Current Page redirects to bulk delete when multiple pages selected
- Pages stored in `pages` table (id, title, parent_id, sort_order, timestamps)
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

---

### Module 3: Content Blocks — Text & Styling
- Pages composed of **content blocks** on a **free-form canvas** (no layout constraints)
- **Text blocks** supporting Markdown syntax (bold, italic, headings, code, links) with `nl2br` extension
- **Preview/edit toggle** — click preview to edit (cursor moves to end); blur to return to rendered view
- Preview updates in real-time as user types (via QStackedWidget switching)
- HTML auto-detection: content starting with `<` is treated as raw HTML
- Toolbar for quick formatting (B/I/H1/H2/code/link/bullet) with vertical separator
- **Font size combo box** ("Size:") in toolbar — sizes [9–32], context-aware via global focus tracking (`QApplication.focusChanged`); applies to header, text content, table cell, or list item depending on focus
- **Keyboard shortcuts:** `Ctrl+B` bold, `Ctrl+I` italic, formatting buttons for H1/H2/code/link/bullet
- Stored in `content_blocks` table (id, page_id, block_type, content_markdown, sort_order, pos_x, pos_y, width, height, header, header_font_size, content_font_size, header_align_h, header_align_v, header_height)
- Auto-save on content change (debounced, default 1s interval; timer interval updates immediately on settings change)
- **Free-form positioning** — drag "⋮⋮" handle **or header area** to move blocks anywhere within canvas bounds
- **Z-order** — clicking a block brings it to the front
- **Resize handle** at bottom: height (vertical drag), width (horizontal drag)
- **Right-edge resize** — hover right edge (↔ cursor), click and drag to change width
- **Corner resize** — bottom-right 24px corner does 2D resize (width + height simultaneously)
- **Infinite vertical scroll** — canvas extends when scrolling near the bottom (within 300px → +500px); no horizontal scrollbar
- **Right-edge boundary** — blocks cannot be dragged or resized past the right edge of the canvas
- Block position (`pos_x`, `pos_y`) persisted in DB and restored on page load
- **Block placement at click position** — clicking canvas stores position; next block created at that position
- **Auto-grid layout** — blocks with default position (0,0) auto-arranged in 5-column grid (280px H / 200px V spacing)
- **Block multi-select on canvas** — Ctrl+click / Shift+click selects multiple blocks; selected blocks show 2px indigo border with light background
- **Block delete via keyboard** — `Delete` key or `Ctrl+D` (when not in text edit) deletes all selected blocks
- **Block auto-fit to content** — blocks auto-resize height to fit content when not manually resized; `_manual_resize` flag disables auto-fit once user manually resizes
- **Default block dimensions** — height: 200px, width: 1/3 of canvas
- **Scroll to newest block** after creation via `ensureWidgetVisible`
- **Embedded Task Lists in Text Blocks** — text blocks can contain embedded checkbox task lists; each list has drag handle, "Tasks" label, "+ Add Task" button, "×" remove button; tasks stored via `InMemoryTaskRepo` and serialized as JSON within block content
- **Editable Block Header** — each block has an editable header (QTextEdit); Enter accepts edit, Tab moves focus; placeholder shows block type; header text only persisted if different from default
- **Block header horizontal alignment** — ⫷ left / ⫿ center / ⫸ right buttons; persisted in `header_align_h`
- **Block header vertical alignment** — ↥ top / ↕ middle / ↧ bottom buttons; persisted in `header_align_v`; vertical alignment buttons only enabled when header is focused
- **Block header font size** — toolbar Size combo applies to header when focused; adjusts header edit height and container height
- **Block header height resize** — dedicated 8px resize handle between header and body; persisted in `header_height`
- **Alignment button sync** — alignment buttons synchronize to reflect current alignment of focused element on focus change
- **List/checkbox blocks** wrapped in QScrollArea for internal scrolling when content exceeds block height

**Acceptance criteria:**
- Text blocks persist Markdown content and render formatted output
- Toolbar buttons apply correct Markdown wrapping
- Blocks can be freely dragged and positioned within canvas bounds; overlapping supported
- Clicking a block brings it to the front
- Blocks can be resized: vertically (bottom), horizontally (bottom or right edge), or both (corner)
- Canvas extends vertically on scroll (even with no blocks); no horizontal scrollbar
- Right edge acts as a hard boundary for both drag and resize
- Auto-save triggers within 1 second of stopping typing
- Block positions survive app restart
- Font size combo applies to the correct element based on focus
- Block headers can be edited, aligned (H/V), font-sized, and height-resized; all persist
- Multiple blocks can be selected on canvas and deleted via Delete/Ctrl+D
- Embedded task lists in text blocks persist across sessions
- New blocks placed at last canvas click position; default-position blocks auto-grid
- Auto-fit adjusts block height to content; manual resize disables auto-fit
- Drag works from both the drag handle and the header area

---

### Module 4: Content Blocks — Tables, Lists & Checkboxes
- **Table blocks**: dynamic rows/columns (+ Row / - Row / + Col / - Col), cells accept plain text
- **Table header row** — toggleable via "+ Header" / "- Header" buttons; header cells are bold, centered, gray background; default labels "Column N"; header content is editable; header changes trigger auto-save
- **Table row numbers** — toggleable via "+ Row #" / "- Row #" buttons; 40px-wide leftmost column with sequential numbers; top-left shows "#" when headers enabled; styled with gray background, bold 11px font
- **Table multi-cell selection** — Ctrl+click (toggle) / Shift+click (range from anchor); selected cells highlighted with blue border/background
- **Table cell keyboard navigation** — Tab/Shift+Tab moves between cells (wraps between header and data); Tab in last cell of last row auto-adds new row; Delete/Backspace clears selected cells; Escape clears selection
- **Table minimum protection** — "- Row" won't delete last row (unless headers exist); "- Col" won't reduce below 1 (or below header count)
- **Table content serialization** — Markdown pipe-delimited format with optional JSON metadata line for header/row-number state
- **Embedded Task Lists in Table Cells** — "+ List" while cell focused adds task list to cell; cell's text edit replaced with TaskWidget; tasks serialized as JSON (`{"_type": "tasks", "tasks": [...]}`); block header "+ Add Task" dynamically shows/hides based on active cell's task list state
- **List blocks** (checkbox type) with per-task:
  - Checkbox toggle (check/uncheck)
  - **Multi-line text area** (`QTextEdit` replaces `QLineEdit`) with auto-grow
  - Recurrence dropdown: `none` / `daily` / `weekly` / `monthly`
  - **Delete per task** via "X" button (30px wide, red hover styling)
  - **"+ Add Task"** button in the block header (alongside alignment & delete-block buttons)
  - **Column resize** — drag vertical `⋮` handle between text area and sidebar to change text width (min 100 px)
  - **Row resize** — drag horizontal handle at bottom of each task row to set fixed height (overrides auto-grow)
  - **Sidebar layout** — sidebar (Recur combobox + Delete button) fixed at right edge, vertically aligned across all rows
- **Context-aware "+ List" button** — if table cell focused → adds task list to cell; if text block focused → adds embedded list to block; otherwise → creates new checkbox block
- **Recurring tasks** — when checked, a copy is created with shifted `due_date` (daily=+1d, weekly=+7d, monthly=+30d); monthly uses fixed 30-day offset (not calendar months)
- `tasks` table: id, content_block_id, text, is_checked, recurrence_type (none/daily/weekly/monthly), due_date, parent_task_id (FK self, nullable), sort_order
- **In-memory task storage** — `InMemoryTaskRepo` used for embedded task lists (serialized within parent block content rather than separate DB rows); pluggable via `task_repo` parameter on `TaskWidget`
- Auto-grow uses `QTimer.singleShot(0, ...)` for correct initial sizing after layout

**Acceptance criteria:**
- Tables can have rows/columns added and removed
- Table header row can be toggled on/off with correct styling and persistence
- Row number column can be toggled on/off with correct styling and persistence
- Multi-cell selection works with Ctrl+click and Shift+click
- Tab/Shift+Tab navigates between cells; Tab at last cell auto-adds row
- Delete/Backspace clears selected cells; Escape clears selection
- Checkboxes toggle visual state (checked/unchecked)
- Recurring tasks create a copy with next period's date when checked (monthly = +30d)
- Tasks can be individually added and deleted
- Auto-grow expands task row height on multi-line text; does not shrink
- Column resize handle changes only the edit width; sidebar stays at a fixed right position
- Row resize handle overrides auto-grow height; task row does not auto-grow while fixed
- Sidebar buttons (Recur + Delete per-task) are aligned vertically across all rows
- Embedded task lists in table cells persist across sessions
- Context-aware "+ List" button adds to correct target based on focus

---

### Module 5: Template System
- Save any page (including its content blocks) as a **template**
- Browse/insert templates into a **single page** via toolbar **"Template"** button
- Templates displayed as "Name (Category)" in selection dialogs
- **Bulk insert** — select multiple pages in sidebar, right-click **"Insert Template into Selected (N)"**
- **Confirmation messages** — save: "Template '{name}' saved."; bulk insert: "Template '{name}' inserted into {N} page(s)."
- **Info messages** — "No templates saved yet." when inserting with no templates; "Select a page first." when saving with no page loaded
- `templates` table: id, name, category (default: "General"), content_json (text), created_at
- Templates ordered by category then name in queries

**Acceptance criteria:**
- Saving a template captures all content blocks of the page
- Inserting a template appends its blocks to the current page (or to all selected pages)
- Templates survive app restart (persisted in SQLite)
- Confirmation and info messages shown at appropriate times

---

### Module 6: UI Polish & Data Persistence
- **Auto-save** on all content changes (timer-based, configurable interval; applied immediately on settings change)
- **Collapsible sidebar** via View → Toggle Sidebar
- **Resizable splitter** panels between sidebar and editor (stretch factor 1:3; initial sizes from `sidebar_width` setting)
- **Page title display** in editor toolbar (bold label; "Select a page" when no page loaded)
- **Keyboard shortcuts:**

  | Shortcut | Context | Action |
  |----------|---------|--------|
  | `Ctrl+N` | Global | New Page (as child if pages selected) |
  | `Ctrl+Shift+N` | Global | New Child Page |
  | `Ctrl+S` | Global | Save |
  | `Delete` | Sidebar | Delete page(s) — single or bulk |
  | `Delete` | Editor (blocks selected) | Delete selected block(s) |
  | `Ctrl+D` | Sidebar | Delete Selected (bulk) |
  | `Ctrl+D` | Editor (not in text edit) | Delete selected block(s) |
  | `Ctrl+Shift+Z` | Global | Undo Delete |
  | `Ctrl+U` | Global | Undo Delete |
  | `Ctrl+Z` | Sidebar focus only | Undo Delete |
  | `Ctrl+Shift+B` | Global | Bulk Create Pages |
  | `Ctrl+B` | Text block focused | Bold |
  | `Ctrl+I` | Text block focused | Italic |
  | `Ctrl+Q` | Global | Exit |
  | `Tab` | Table cell | Next cell |
  | `Shift+Tab` | Table cell | Previous cell |
  | `Delete`/`Backspace` | Table cells selected | Clear selected cells |
  | `Escape` | Table cell | Clear cell selection |
  | `Enter` | Block header | Accept header edit |
  | `Tab` | Block header | Move focus out |

- **Settings dialog** (File → Settings): week start day, auto-save interval (500–10000ms, step 500), font size (10–32, requires restart); shows "Settings saved. Restart to apply font size changes." on save
- **Additional persisted settings** (not in dialog): `sidebar_width` (default: 250), `theme` (default: "light")
- Touch-friendly controls for tablet (larger hit targets, swipe gestures)

**Acceptance criteria:**
- All keyboard shortcuts work and are discoverable
- Sidebar collapse/expand is smooth
- Touch targets are at least 44×44px
- Font size combo and alignment buttons target the correct element based on focus
- Settings auto-save interval change applies immediately

---

## Architectural Choices

- **Data layer**: SQLite via `sqlite3` (stdlib) with a thin repository pattern (`page_repo.py`, `block_repo.py`, `task_repo.py`, `template_repo.py`, `in_memory_task_repo.py`)
- **Content model**: Pages own an ordered list of content blocks. Each block has a type and a Markdown payload. Tables store their structure as Markdown with delimiters plus optional JSON metadata for headers/row-numbers.
- **Embedded task lists**: Text blocks and table cells can contain embedded task lists serialized as JSON within the parent content. `InMemoryTaskRepo` provides the same interface as `TaskRepo` but stores tasks in-memory (pluggable via `task_repo` parameter).
- **Task model**: Tasks belong to a content block. Recurrence is resolved at query time — when a recurring task is checked, a new task is inserted with a shifted `due_date`. Monthly = fixed 30 days.
- **Templates**: Serialize the full block structure of a page as JSON into a single column. Category field (default: "General") for future grouping.
- **Undo model**: In-memory `UndoManager` singleton stores deleted pages/blocks/tasks with timestamps; auto-prunes entries older than 15 minutes. On undo, restores with original DB IDs (safe under SQLite `AUTOINCREMENT` which never recycles old IDs). Page undo recursively restores full child hierarchy.
- **Focus tracking**: `PageEditor` connects to `QApplication.focusChanged` to track which block/part has focus, enabling context-aware font size and alignment controls.
- **Block serialization**: Text blocks with embedded lists serialize as `{"text": "<html>", "task_lists": [...]}`. Table cells with tasks serialize as `{"_type": "tasks", "tasks": [...]}`. Block width only persisted if explicitly fixed; header text only persisted if different from default.

---

## Database Schema

| Table | Key Columns |
|-------|-------------|
| `pages` | id (PK), title (DEFAULT 'Untitled'), parent_id (FK self, nullable, CASCADE), sort_order, created_at, updated_at |
| `content_blocks` | id (PK), page_id (FK, CASCADE), block_type (text/table/list/checkbox), content_markdown (DEFAULT ''), sort_order, pos_x, pos_y, width, height, header, header_font_size, content_font_size, header_align_h (DEFAULT 'left'), header_align_v (DEFAULT 'center'), header_height |
| `tasks` | id (PK), content_block_id (FK, CASCADE), text, is_checked (bool), recurrence_type (none/daily/weekly), due_date (nullable), parent_task_id (FK self, nullable, CASCADE), sort_order |
| `templates` | id (PK), name, category (DEFAULT 'General'), content_json (text), created_at |

- All foreign keys use `ON DELETE CASCADE`
- `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON` on every connection
- `sqlite3.Row` row factory for dictionary-like access
- Schema migrations via `ALTER TABLE ... ADD COLUMN` with try/except
- Auto-calculated `sort_order` on create (MAX + 1 for given parent/block)

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
