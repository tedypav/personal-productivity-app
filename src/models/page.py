from dataclasses import dataclass
from typing import Optional


@dataclass
class Page:
    id: Optional[int] = None
    title: str = "Untitled"
    parent_id: Optional[int] = None
    sort_order: int = 0
    page_type: str = "page"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
