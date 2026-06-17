"""Page data model — represents a page or folder in the hierarchy."""

from dataclasses import dataclass


@dataclass
class Page:
    """A page or folder in the sidebar tree.

    Pages form a self-referential hierarchy via parent_id.
    page_type distinguishes 'page', 'folder', 'template_page'.
    """

    id: int | None = None
    title: str = "Untitled"
    parent_id: int | None = None
    sort_order: int = 0
    page_type: str = "page"
    created_at: str | None = None
    updated_at: str | None = None
