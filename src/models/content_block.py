from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ContentBlock:
    id: Optional[int] = None
    page_id: Optional[int] = None
    block_type: str = "text"
    content_markdown: str = ""
    sort_order: int = 0
    height: Optional[int] = None
    width: Optional[int] = None
    header: Optional[str] = None
    header_font_size: Optional[int] = None
    content_font_size: Optional[int] = None
    pos_x: int = 0
    pos_y: int = 0
