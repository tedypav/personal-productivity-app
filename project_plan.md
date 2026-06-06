# Personal Productivity App — Project Plan

## Tech Stack
- **UI:** Python + PyQt6
- **Storage:** SQLite
- **Text Editing:** Markdown-based
- **Page Organization:** Sidebar tree / nested hierarchy

---

## Modules

### Module 1: Core Architecture & Project Setup
- PyQt6 application scaffold with `QMainWindow`
- SQLite database initialization with schema migrations
- Main layout: **Sidebar tree (left)** + **Page editor (right)**
- Config/settings file for user preferences

### Module 2: Page Management
- CRUD operations (create, rename, delete, reorder pages)
- **Nested hierarchy** via `parent_id` — drag-to-reorder or context menu
- **Bulk page creation** — generate N pages from a template or naming pattern (e.g., "Week 1" through "Week 12")
- Pages stored in `pages` table (id, title, parent_id, sort_order, timestamps)

### Module 3: Content Blocks — Text & Styling
- Pages composed of ordered **content blocks** (like Notion's drag-and-drop rows)
- **Text blocks** supporting Markdown syntax (bold, italic, headings, code, links)
- Toolbar for quick formatting (B/I/H1/H2/bullet)
- Stored in `content_blocks` table (id, page_id, block_type, content_markdown, sort_order)

### Module 4: Content Blocks — Tables, Lists & Checkboxes
- **Table blocks**: dynamic rows/columns, cells accept Markdown text **and** nested lists
- **List blocks** with checkbox toggles (check/uncheck visually)
- **Recurring tasks** — tasks marked `recurrence: weekly` auto-duplicate to the next week on check
- `tasks` table: id, content_block_id, text, is_checked, recurrence_type (none/daily/weekly), due_date, sort_order

### Module 5: Template System
- Save any page (including its content blocks) as a **template**
- Browse/insert templates into a page via a dialog
- `templates` table: id, name, category, content_snapshot (JSON)
- Bulk page creation sources from templates

### Module 6: UI Polish & Data Persistence
- Auto-save on content change
- Collapsible sidebar, resizable panels
- Keyboard shortcuts (Ctrl+N page, Ctrl+S save, etc.)

---

## Database Schema

| Table | Key Columns |
|-------|-------------|
| `pages` | id, title, parent_id (nullable), sort_order, created_at, updated_at |
| `content_blocks` | id, page_id (FK), block_type (text/table/list/checkbox), content_markdown, sort_order |
| `tasks` | id, content_block_id (FK), text, is_checked, recurrence_type, due_date, parent_task_id, sort_order |
| `templates` | id, name, category, content_json, created_at |
