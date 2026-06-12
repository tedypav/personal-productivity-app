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


def _add_column(conn, table: str, column_def: str):
    col_name = column_def.split()[0]
    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    if col_name not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")


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
    """)

    cursor.executescript("""
        CREATE INDEX IF NOT EXISTS idx_pages_parent ON pages(parent_id);
        CREATE INDEX IF NOT EXISTS idx_pages_sort ON pages(sort_order);
    """)

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS page_objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL
                REFERENCES pages(id) ON DELETE CASCADE,
            object_type TEXT NOT NULL,
            content TEXT NOT NULL DEFAULT '{}',
            is_checked INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    cursor.executescript("""
        CREATE INDEX IF NOT EXISTS idx_objects_page ON page_objects(page_id);
    """)

    _add_column(conn, "pages", "page_type TEXT NOT NULL DEFAULT 'page'")

    conn.commit()
