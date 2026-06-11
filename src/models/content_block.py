from dataclasses import dataclass


@dataclass
class ContentBlock:
    id: int | None = None
    page_id: int | None = None
    block_type: str = "text"
    content_markdown: str = ""
    sort_order: int = 0
    height: int | None = None
    width: int | None = None
    header: str | None = None
    header_font_size: int | None = None
    header_align_h: str = "left"
    header_align_v: str = "center"
    header_height: int | None = None
    content_font_size: int | None = None
    pos_x: int = 0
    pos_y: int = 0

    def __post_init__(self):
        self.header_font_size = self._normalize_font_size(self.header_font_size)
        self.content_font_size = self._normalize_font_size(self.content_font_size)

    @staticmethod
    def _normalize_font_size(value: int | None) -> int | None:
        if value is None:
            return None
        try:
            size = int(value)
        except (TypeError, ValueError):
            return None
        return size if size >= 1 else None
