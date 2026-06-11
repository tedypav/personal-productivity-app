import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.db")

_connection = None


def get_connection():
    global _connection
    if _connection is not None:
        try:
            _connection.execute("SELECT 1")
            return _connection
        except sqlite3.ProgrammingError:
            _connection = None
    _connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    _connection.row_factory = sqlite3.Row
    _connection.execute("PRAGMA journal_mode=WAL")
    _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


def close_connection():
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None


def reset_connection():
    close_connection()


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT 'Untitled',
            parent_id INTEGER REFERENCES pages(id) ON DELETE CASCADE,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS content_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL
                REFERENCES pages(id) ON DELETE CASCADE,
            block_type TEXT NOT NULL
                CHECK(block_type IN ('text','table','list','checkbox')),
            content_markdown TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_block_id INTEGER NOT NULL
                REFERENCES content_blocks(id) ON DELETE CASCADE,
            text TEXT NOT NULL DEFAULT '',
            is_checked INTEGER NOT NULL DEFAULT 0,
            recurrence_type TEXT NOT NULL DEFAULT 'none'
                CHECK(recurrence_type IN ('none','daily','weekly')),
            due_date TEXT,
            parent_task_id INTEGER REFERENCES tasks(id)
                ON DELETE CASCADE,
            sort_order INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'General',
            content_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    cursor.executescript("""
        CREATE INDEX IF NOT EXISTS idx_blocks_page ON content_blocks(page_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_block ON tasks(content_block_id);
        CREATE INDEX IF NOT EXISTS idx_pages_parent ON pages(parent_id);
        CREATE INDEX IF NOT EXISTS idx_pages_sort ON pages(sort_order);
        CREATE INDEX IF NOT EXISTS idx_tasks_sort ON tasks(sort_order);
    """)

    try:
        conn.execute("ALTER TABLE content_blocks ADD COLUMN height INTEGER")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE content_blocks ADD COLUMN width INTEGER")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE content_blocks ADD COLUMN header TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE content_blocks ADD COLUMN header_font_size INTEGER")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE content_blocks ADD COLUMN content_font_size INTEGER")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE content_blocks ADD COLUMN pos_x INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE content_blocks ADD COLUMN pos_y INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute(
            "ALTER TABLE content_blocks ADD COLUMN header_align_h TEXT DEFAULT 'left'"
        )
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute(
            "ALTER TABLE content_blocks ADD COLUMN header_align_v TEXT DEFAULT 'center'"
        )
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE content_blocks ADD COLUMN header_height INTEGER")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute(
            "ALTER TABLE pages ADD COLUMN page_type TEXT NOT NULL DEFAULT 'page'"
        )
    except sqlite3.OperationalError:
        pass

    conn.execute(
        "UPDATE content_blocks SET header_font_size = NULL WHERE header_font_size < 1"
    )
    conn.execute(
        "UPDATE content_blocks SET content_font_size = NULL WHERE content_font_size < 1"
    )

    conn.commit()
    conn.close()
