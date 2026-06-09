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
    header_align_h: str = "left"
    header_align_v: str = "center"
    header_height: Optional[int] = None
    content_font_size: Optional[int] = None
    pos_x: int = 0
    pos_y: int = 0

    def __post_init__(self):
        self.header_font_size = self._normalize_font_size(self.header_font_size)
        self.content_font_size = self._normalize_font_size(self.content_font_size)

    @staticmethod
    def _normalize_font_size(value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        try:
            size = int(value)
        except (TypeError, ValueError):
            return None
        return size if size >= 1 else None
