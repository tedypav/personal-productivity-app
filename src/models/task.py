from dataclasses import dataclass


@dataclass
class Task:
    id: int | None = None
    content_block_id: int | None = None
    text: str = ""
    is_checked: bool = False
    recurrence_type: str = "none"
    due_date: str | None = None
    parent_task_id: int | None = None
    sort_order: int = 0
