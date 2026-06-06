from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ContentBlock:
    id: Optional[int] = None
    page_id: Optional[int] = None
    block_type: str = "text"
    content_markdown: str = ""
    sort_order: int = 0
