from src.database import get_connection
from src.models.content_block import ContentBlock


class BlockRepo:
    @staticmethod
    def get_by_page(page_id: int) -> list[ContentBlock]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM content_blocks WHERE page_id=? ORDER BY sort_order",
            (page_id,),
        ).fetchall()
        conn.close()
        return [ContentBlock(**dict(r)) for r in rows]

    @staticmethod
    def create(block: ContentBlock) -> int:
        conn = get_connection()
        max_order = conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1"
            " FROM content_blocks WHERE page_id=?",
            (block.page_id,),
        ).fetchone()[0]
        cursor = conn.execute(
            "INSERT INTO content_blocks"
            " (page_id, block_type, content_markdown,"
            " sort_order, height, width, header,"
            " header_font_size, header_align_h,"
            " header_align_v, header_height,"
            " content_font_size, pos_x, pos_y)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                block.page_id,
                block.block_type,
                block.content_markdown,
                max_order,
                block.height,
                block.width,
                block.header,
                block.header_font_size,
                block.header_align_h,
                block.header_align_v,
                block.header_height,
                block.content_font_size,
                block.pos_x,
                block.pos_y,
            ),
        )
        conn.commit()
        block_id = cursor.lastrowid
        block.id = block_id
        conn.close()
        return block_id

    @staticmethod
    def update(block: ContentBlock):
        conn = get_connection()
        conn.execute(
            "UPDATE content_blocks SET content_markdown=?,"
            " block_type=?, sort_order=?, height=?, width=?,"
            " header=?, header_font_size=?,"
            " header_align_h=?, header_align_v=?,"
            " header_height=?, content_font_size=?,"
            " pos_x=?, pos_y=? WHERE id=?",
            (
                block.content_markdown,
                block.block_type,
                block.sort_order,
                block.height,
                block.width,
                block.header,
                block.header_font_size,
                block.header_align_h,
                block.header_align_v,
                block.header_height,
                block.content_font_size,
                block.pos_x,
                block.pos_y,
                block.id,
            ),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def delete(block_id: int):
        conn = get_connection()
        conn.execute("DELETE FROM content_blocks WHERE id=?", (block_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def delete_by_page(page_id: int):
        conn = get_connection()
        conn.execute("DELETE FROM content_blocks WHERE page_id=?", (page_id,))
        conn.commit()
        conn.close()
