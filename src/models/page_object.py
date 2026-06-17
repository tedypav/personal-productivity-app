"""PageObject data model — polymorphic content block on a page."""

from dataclasses import dataclass


@dataclass
class PageObject:
    """A content block belonging to a page.

    object_type discriminates the block kind:
    - 'checkbox': standalone checklist item
    - 'checklist_meta': metadata for a checklist widget
    - 'table_meta': metadata for a table widget
    - 'textbox_meta': metadata for a textbox widget

    content stores the block-specific payload as a JSON string.
    sort_order encodes the parent block ID via (block_id * 100 + offset).
    """

    id: int | None = None
    page_id: int | None = None
    object_type: str = "checkbox"
    content: str = "{}"
    is_checked: bool = False
    sort_order: int = 0
    created_at: str | None = None
