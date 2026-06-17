"""SQLite database connection and schema management."""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.db")

_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    """Return the singleton SQLite connection, creating it if necessary.

    Enables WAL journal mode and foreign key enforcement on first connect.
    Self-heals a closed connection by detecting ProgrammingError.
    """
    global _connection
    if _connection is not None:
        try:
            _connection.execute("SELECT 1")
            return _connection
        except sqlite3.ProgrammingError:
            _connection = None
    _connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    # NOTE: App must remain single-threaded. No threading lock is used.
    _connection.row_factory = sqlite3.Row
    _connection.execute("PRAGMA journal_mode=WAL")
    _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


def close_connection() -> None:
    """Close the singleton SQLite connection if open."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None


def reset_connection() -> None:
    """Alias for close_connection(). Used in tests."""
    close_connection()


def _add_column(conn: sqlite3.Connection, table: str, column_def: str) -> None:
    """Add a column to a table if it doesn't already exist."""
    col_name = column_def.split()[0]
    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    if col_name not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")


def init_db() -> None:
    """Create database tables and run schema migrations.

    Safe to call multiple times — uses CREATE IF NOT EXISTS and
    column-existence checks for incremental evolution.
    """
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
