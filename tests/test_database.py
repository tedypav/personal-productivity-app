import sqlite3

import pytest

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

    def test_creates_content_blocks_table(self):
        init_db()
        conn = get_connection()
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        conn.close()
        assert "content_blocks" in tables

    def test_creates_tasks_table(self):
        init_db()
        conn = get_connection()
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        conn.close()
        assert "tasks" in tables

    def test_creates_templates_table(self):
        init_db()
        conn = get_connection()
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        conn.close()
        assert "templates" in tables

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

    def test_migrations_idempotent(self):
        init_db()
        init_db()
        conn = get_connection()
        cols = [
            r[1] for r in conn.execute("PRAGMA table_info(content_blocks)").fetchall()
        ]
        conn.close()
        assert "height" in cols
        assert "width" in cols
        assert "header" in cols
        assert "pos_x" in cols
        assert "pos_y" in cols

    def test_pages_has_page_type_column(self):
        init_db()
        conn = get_connection()
        cols = [r[1] for r in conn.execute("PRAGMA table_info(pages)").fetchall()]
        conn.close()
        assert "page_type" in cols

    def test_font_size_cleanup(self):
        init_db()
        conn = get_connection()
        pid = conn.execute("INSERT INTO pages (title) VALUES ('test')").lastrowid
        bid = conn.execute(
            "INSERT INTO content_blocks"
            " (page_id, block_type,"
            " header_font_size, content_font_size)"
            " VALUES (?, 'text', 0, -1)",
            (pid,),
        ).lastrowid
        conn.commit()
        init_db()
        row = conn.execute(
            "SELECT header_font_size, content_font_size FROM content_blocks WHERE id=?",
            (bid,),
        ).fetchone()
        conn.close()
        assert row[0] is None
        assert row[1] is None

    def test_foreign_key_cascade(self):
        init_db()
        conn = get_connection()
        pid = conn.execute("INSERT INTO pages (title) VALUES ('test')").lastrowid
        conn.execute(
            "INSERT INTO content_blocks" " (page_id, block_type)" " VALUES (?, 'text')",
            (pid,),
        )
        conn.commit()
        conn.execute("DELETE FROM pages WHERE id=?", (pid,))
        conn.commit()
        remaining = conn.execute(
            "SELECT COUNT(*) FROM content_blocks WHERE page_id=?", (pid,)
        ).fetchone()[0]
        conn.close()
        assert remaining == 0

    def test_block_type_check_constraint(self):
        init_db()
        conn = get_connection()
        pid = conn.execute("INSERT INTO pages (title) VALUES ('test')").lastrowid
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO content_blocks"
                " (page_id, block_type)"
                " VALUES (?, 'invalid')",
                (pid,),
            )
        conn.close()

    def test_recurrence_type_check_constraint(self):
        init_db()
        conn = get_connection()
        pid = conn.execute("INSERT INTO pages (title) VALUES ('test')").lastrowid
        bid = conn.execute(
            "INSERT INTO content_blocks (page_id, block_type) VALUES (?, 'text')",
            (pid,),
        ).lastrowid
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO tasks"
                " (content_block_id,"
                " recurrence_type)"
                " VALUES (?, 'yearly')",
                (bid,),
            )
        conn.close()
