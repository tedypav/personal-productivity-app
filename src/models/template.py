from dataclasses import dataclass


@dataclass
class Template:
    id: int | None = None
    name: str = ""
    category: str = "General"
    content_json: str = "[]"
    created_at: str | None = None
