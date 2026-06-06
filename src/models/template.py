from dataclasses import dataclass
from typing import Optional


@dataclass
class Template:
    id: Optional[int] = None
    name: str = ""
    category: str = "General"
    content_json: str = "[]"
    created_at: Optional[str] = None
