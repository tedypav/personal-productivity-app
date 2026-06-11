from dataclasses import dataclass


@dataclass
class Page:
    id: int | None = None
    title: str = "Untitled"
    parent_id: int | None = None
    sort_order: int = 0
    page_type: str = "page"
    created_at: str | None = None
    updated_at: str | None = None
