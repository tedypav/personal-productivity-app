import sqlite3

from src.database import get_connection, init_db


class TestGetConnection:
    def test_returns_connection(self):
        conn = get_connection()
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_row_factory(self):
        conn = get_connection()
        assert conn.row_factory == sqlite3.Row
        conn.close()

    def test_wal_journal_mode(self):
        conn = get_connection()
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"
        conn.close()

    def test_foreign_keys_enabled(self):
        conn = get_connection()
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk == 1
        conn.close()


class TestInitDb:
    def test_creates_pages_table(self):
        init_db()
        conn = get_connection()
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        conn.close()
        assert "pages" in tables

    def test_idempotent(self):
        init_db()
        conn = get_connection()
        count_before = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0]
        conn.close()
        init_db()
        conn = get_connection()
        count_after = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0]
        conn.close()
        assert count_after == count_before

    def test_pages_has_page_type_column(self):
        init_db()
        conn = get_connection()
        cols = [r[1] for r in conn.execute("PRAGMA table_info(pages)").fetchall()]
        conn.close()
        assert "page_type" in cols
