from dataclasses import dataclass


@dataclass
class PageObject:
    id: int | None = None
    page_id: int | None = None
    object_type: str = "checkbox"
    content: str = "{}"
    is_checked: bool = False
    sort_order: int = 0
    created_at: str | None = None
