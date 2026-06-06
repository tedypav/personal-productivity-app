from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    id: Optional[int] = None
    content_block_id: Optional[int] = None
    text: str = ""
    is_checked: bool = False
    recurrence_type: str = "none"
    due_date: Optional[str] = None
    parent_task_id: Optional[int] = None
    sort_order: int = 0
