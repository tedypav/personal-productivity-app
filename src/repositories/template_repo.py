from src.database import get_connection
from src.models.template import Template


class TemplateRepo:
    @staticmethod
    def get_all() -> list[Template]:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM templates ORDER BY category, name").fetchall()
        conn.close()
        return [Template(**dict(r)) for r in rows]

    @staticmethod
    def get_by_id(template_id: int) -> Template | None:
        conn = get_connection()
        row = conn.execute("SELECT * FROM templates WHERE id=?", (template_id,)).fetchone()
        conn.close()
        return Template(**dict(row)) if row else None

    @staticmethod
    def create(template: Template) -> int:
        conn = get_connection()
        cursor = conn.execute(
            "INSERT INTO templates (name, category, content_json) VALUES (?, ?, ?)",
            (template.name, template.category, template.content_json)
        )
        conn.commit()
        template_id = cursor.lastrowid
        conn.close()
        return template_id

    @staticmethod
    def delete(template_id: int):
        conn = get_connection()
        conn.execute("DELETE FROM templates WHERE id=?", (template_id,))
        conn.commit()
        conn.close()
