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

**Deferred until after MVP:**
- AI integration (OpenAI/Anthropic)
- Mobile phone optimization

---

## Modules

### Module 1: Core Architecture & Project Setup
- PyQt6 application scaffold with `QMainWindow`
- SQLite database initialization with schema migrations
- Main layout: **Sidebar tree (left)** + **Page editor (right)**
- Config/settings file for user preferences
- Responsive layout that adapts to tablet dimensions

**Acceptance criteria:**
- App launches showing a split-pane layout
- Sidebar is collapsible
- Window resizes gracefully (test at 1024×768 and 1920×1080)

---

### Module 2: Page Management
- CRUD operations (create, rename, delete, reorder pages)
- **Nested hierarchy** via `parent_id` — drag-to-reorder or context menu
- **Bulk date-based page creation** — dialog with three modes:

  | Mode | Page Name | Logic |
  |------|-----------|-------|
  | **Days** | `YYYY-MM-DD` | User picks start & end date → one page per day |
  | **Weeks** | `YYYY-MM-DD - YYYY-MM-DD` | User picks a reference date + start-of-week day (Mon/Tue/.../Sun) → find nearest past start-of-week on or before ref date → generate N weekly pages forward from that start |
  | **Years** | `YYYY` | User picks start & end year → one page per year |

- Pages stored in `pages` table (id, title, parent_id, sort_order, timestamps)

**Acceptance criteria:**
- Pages can be created, renamed, deleted, and nested under parents
- Bulk creation generates correct page names per the format table
- Week calculation correctly snaps to the user-chosen start-of-week day

---

### Module 3: Content Blocks — Text & Styling
- Pages composed of ordered **content blocks** (like Notion's drag-and-drop rows)
- **Text blocks** supporting Markdown syntax (bold, italic, headings, code, links)
- Toolbar for quick formatting (B/I/H1/H2/bullet)
- Stored in `content_blocks` table (id, page_id, block_type, content_markdown, sort_order)
- Auto-save on content change (debounced)

**Acceptance criteria:**
- Text blocks persist Markdown content and render formatted output
- Toolbar buttons apply correct Markdown wrapping
- Auto-save triggers within 1 second of stopping typing

---

### Module 4: Content Blocks — Tables, Lists & Checkboxes
- **Table blocks**: dynamic rows/columns, cells accept Markdown text **and** nested lists
- **List blocks** with checkbox toggles (check/uncheck visually)
- **Recurring tasks** — tasks marked `recurrence: weekly` auto-duplicate to the next week on check
- `tasks` table: id, content_block_id, text, is_checked, recurrence_type (none/daily/weekly), due_date, sort_order

**Acceptance criteria:**
- Tables can have rows/columns added and removed
- Checkboxes toggle visual state (checked/unchecked)
- Recurring tasks create a copy with next week's date when checked

---

### Module 5: Template System
- Save any page (including its content blocks) as a **template**
- Browse/insert templates into a page via a dialog
- `templates` table: id, name, category, content_snapshot (JSON)

**Acceptance criteria:**
- Saving a template captures all content blocks of the page
- Inserting a template appends its blocks to the current page
- Templates survive app restart (persisted in SQLite)

---

### Module 6: UI Polish & Data Persistence
- Auto-save on all content changes
- Collapsible sidebar, resizable splitter panels
- Keyboard shortcuts (Ctrl+N new page, Ctrl+S save, Del delete, etc.)
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

---

## Database Schema

| Table | Key Columns |
|-------|-------------|
| `pages` | id (PK), title, parent_id (FK self, nullable), sort_order, created_at, updated_at |
| `content_blocks` | id (PK), page_id (FK), block_type (text/table/list/checkbox), content_markdown, sort_order |
| `tasks` | id (PK), content_block_id (FK), text, is_checked (bool), recurrence_type (none/daily/weekly), due_date (nullable), parent_task_id (FK self, nullable), sort_order |
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
