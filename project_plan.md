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
- Tables, lists, checkboxes, recurring tasks
- Template save and insert
- Auto-save and responsive layout (desktop + tablet)
- Bulk date-based page creation (days/weeks/years)
- No-confirmation deletion with 15-minute undo
- Multi-select sidebar with bulk delete & bulk template insert
- Keyboard shortcuts for all frequent actions

**Deferred until after MVP:**
- AI integration (OpenAI/Anthropic)
- Mobile phone optimization

---

## Modules

### Module 1: Core Architecture & Project Setup
- PyQt6 application scaffold with `QMainWindow`
- SQLite database initialization with schema migrations
- Main layout: **Sidebar tree (left)** + **Page editor (right)**
- Config/settings file for user preferences (`settings.json`)
- Responsive layout that adapts to tablet dimensions
- Persisted window geometry preferences

**Acceptance criteria:**
- App launches showing a split-pane layout
- Sidebar is collapsible
- Window resizes gracefully (test at 1024×768 and 1920×1080)
- Settings persist across restarts

---

### Module 2: Page Management
- CRUD operations (create, rename, delete, reorder pages)
- **Nested hierarchy** via `parent_id` — context menu (Move Up/Down)
- **Multi-select** — Ctrl+click / Shift+click for batch operations
- **Bulk delete** — select multiple pages, right-click **Delete Selected (N)**, or `Ctrl+D` / `Delete` key
- **Undo delete** — all deletions (single/bulk, page/block/task) are stored for **15 minutes** and restored via **Edit → Undo Delete** (`Ctrl+Shift+Z`, `Ctrl+U`, or `Ctrl+Z` with sidebar focus); each press undoes one action, supporting multiple undos in sequence
- **New Page as child** — `Ctrl+N` / "+ New Page" creates children under selected page(s); creates root-level page if none selected
- **Bulk time-based page creation** — dialog with three modes; end date dynamically adjusts when start changes (+1d / +7d / +1y)

  | Mode | Page Name | Logic |
  |------|-----------|-------|
  | **Days** | `YYYY-MM-DD` | User picks start & end date → one page per day |
  | **Weeks** | `YYYY-MM-DD - YYYY-MM-DD` | User picks a reference date + start-of-week day (Mon/Tue/.../Sun) → find nearest past start-of-week on or before ref date → generate N weekly pages forward from that start |
  | **Years** | `YYYY` | User picks start & end year → one page per year |

- **Bulk named page creation** — click "+ Bulk Named" → enter base name + count → creates `BaseName 1`, `BaseName 2`, ...
- **Expand/Collapse** — "Show All" / "Hide All" buttons in sidebar; manually collapsed branches persist across refreshes
- Pages stored in `pages` table (id, title, parent_id, sort_order, timestamps)

**Acceptance criteria:**
- Pages can be created, renamed, deleted, and nested under parents
- Multiple pages can be selected and bulk-deleted (undos as single action)
- Undo restores any deletion within 15 minutes
- Bulk creation generates correct page names per the format table
- Week calculation correctly snaps to the user-chosen start-of-week day
- Ctrl+N with selection creates child pages; with no selection creates root-level
- Show/Hide All buttons toggle tree; manual collapse state survives refresh

---

### Module 3: Content Blocks — Text & Styling
- Pages composed of **content blocks** on a **free-form canvas** (no layout constraints)
- **Text blocks** supporting Markdown syntax (bold, italic, headings, code, links)
- **Preview/edit toggle** — click preview to edit; blur to return to rendered view
- Toolbar for quick formatting (B/I/H1/H2/code/link/bullet)
- **Keyboard shortcuts:** `Ctrl+B` bold, `Ctrl+I` italic, formatting buttons for H1/H2/code/link/bullet
- Stored in `content_blocks` table (id, page_id, block_type, content_markdown, sort_order, pos_x, pos_y, width, height, header, header_font_size, content_font_size)
- Auto-save on content change (debounced, default 1s interval)
- **Free-form positioning** — drag "⋮⋮" handle to move blocks anywhere within canvas bounds
- **Z-order** — clicking a block brings it to the front
- **Resize handle** at bottom: height (vertical drag), width (horizontal drag)
- **Right-edge resize** — hover right edge (↔ cursor), click and drag to change width
- **Corner resize** — bottom-right 24px corner does 2D resize (width + height simultaneously)
- **Infinite vertical scroll** — canvas extends when scrolling near the bottom; no horizontal scrollbar
- **Right-edge boundary** — blocks cannot be dragged or resized past the right edge of the canvas
- Block position (`pos_x`, `pos_y`) persisted in DB and restored on page load

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

---

### Module 4: Content Blocks — Tables, Lists & Checkboxes
- **Table blocks**: dynamic rows/columns (+ Row / - Row / + Col / - Col), cells accept plain text
- **List blocks** (checkbox type) with per-task:
  - Checkbox toggle (check/uncheck)
  - Inline text editing
  - Recurrence dropdown: `none` / `daily` / `weekly` / `monthly`
  - **Delete per task** via "X" button
  - **"+ Add Task"** button
- **Recurring tasks** — when checked, a copy is created with shifted `due_date` (daily=+1d, weekly=+7d, monthly=+30d)
- `tasks` table: id, content_block_id, text, is_checked, recurrence_type (none/daily/weekly/monthly), due_date, sort_order

**Acceptance criteria:**
- Tables can have rows/columns added and removed
- Checkboxes toggle visual state (checked/unchecked)
- Recurring tasks create a copy with next period's date when checked
- Tasks can be individually added and deleted

---

### Module 5: Template System
- Save any page (including its content blocks) as a **template**
- Browse/insert templates into a **single page** via toolbar **"Template"** button
- **Bulk insert** — select multiple pages in sidebar, right-click **"Insert Template into Selected (N)"**
- `templates` table: id, name, category, content_json (text), created_at

**Acceptance criteria:**
- Saving a template captures all content blocks of the page
- Inserting a template appends its blocks to the current page (or to all selected pages)
- Templates survive app restart (persisted in SQLite)

---

### Module 6: UI Polish & Data Persistence
- **Auto-save** on all content changes (timer-based, configurable interval)
- **Collapsible sidebar** via View → Toggle Sidebar
- **Resizable splitter** panels between sidebar and editor
- **Keyboard shortcuts:**

  | Shortcut | Action |
  |----------|--------|
  | `Ctrl+N` | New Page (as child if pages selected) |
  | `Ctrl+Shift+N` | New Child Page |
  | `Ctrl+S` | Save |
  | `Delete` | Delete page(s) — single or bulk |
  | `Ctrl+D` | Delete Selected (bulk) |
  | `Ctrl+Shift+Z` | Undo Delete |
  | `Ctrl+U` | Undo Delete |
  | `Ctrl+Z` | Undo Delete (sidebar focus only) |
  | `Ctrl+Shift+B` | Bulk Create Pages |
  | `Ctrl+B` | Bold |
  | `Ctrl+I` | Italic |
  | `Ctrl+Q` | Exit |

- **Settings dialog** (File → Settings): week start day, auto-save interval (500–10000ms), font size (10–32, requires restart)
- Touch-friendly controls for tablet (larger hit targets, swipe gestures)

**Acceptance criteria:**
- All keyboard shortcuts work and are discoverable
- Sidebar collapse/expand is smooth
- Touch targets are at least 44×44px

---

## Architectural Choices

- **Data layer**: SQLite via `sqlite3` (stdlib) with a thin repository pattern (`page_repo.py`, `block_repo.py`, `task_repo.py`, `template_repo.py`)
- **Content model**: Pages own an ordered list of content blocks. Each block has a type and a Markdown payload. Tables store their structure as Markdown with delimiters.
- **Task model**: Tasks belong to a content block. Recurrence is resolved at query time — when a recurring task is checked, a new task is inserted with a shifted `due_date`.
- **Templates**: Serialize the full block structure of a page as JSON into a single column.
- **Undo model**: In-memory `UndoManager` stores deleted pages/blocks/tasks with timestamps; auto-prunes entries older than 15 minutes. On undo, restores with original DB IDs (safe under SQLite `AUTOINCREMENT` which never recycles old IDs).

---

## Database Schema

| Table | Key Columns |
|-------|-------------|
| `pages` | id (PK), title, parent_id (FK self, nullable), sort_order, created_at, updated_at |
| `content_blocks` | id (PK), page_id (FK), block_type (text/table/list/checkbox), content_markdown, sort_order, pos_x, pos_y, width, height, header, header_font_size, content_font_size |
| `tasks` | id (PK), content_block_id (FK), text, is_checked (bool), recurrence_type (none/daily/weekly/monthly), due_date (nullable), parent_task_id (FK self, nullable), sort_order |
| `templates` | id (PK), name, category, content_json (text), created_at |

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
