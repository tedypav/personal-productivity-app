from datetime import datetime, timedelta

from src.database import get_connection

UNDO_DURATION = timedelta(minutes=15)


def capture_page_tree(page_id: int) -> dict | None:
    from src.repositories.block_repo import BlockRepo
    from src.repositories.page_repo import PageRepo
    from src.repositories.task_repo import TaskRepo

    page = PageRepo().get_by_id(page_id)
    if not page:
        return None

    blocks = BlockRepo().get_by_page(page_id)
    block_ids = [b.id for b in blocks if b.id is not None]
    tasks = TaskRepo().get_by_blocks(block_ids)

    return {
        "page": _page_dict(page),
        "blocks": [_block_dict(b) for b in blocks],
        "tasks": [_task_dict(t) for t in tasks],
        "children": _capture_children(page_id),
    }


def _capture_children(parent_id: int) -> list:
    from src.repositories.block_repo import BlockRepo
    from src.repositories.page_repo import PageRepo
    from src.repositories.task_repo import TaskRepo

    result = []
    for child in PageRepo().get_children(parent_id):
        if child.id is None:
            continue
        blocks = BlockRepo().get_by_page(child.id)
        block_ids = [b.id for b in blocks if b.id is not None]
        tasks = TaskRepo().get_by_blocks(block_ids)
        if child.id is not None:
            result.append(
                {
                    "page": _page_dict(child),
                    "blocks": [_block_dict(b) for b in blocks],
                    "tasks": [_task_dict(t) for t in tasks],
                    "children": _capture_children(child.id),
                }
            )
    return result


def _page_dict(page):
    return {
        "id": page.id,
        "title": page.title,
        "parent_id": page.parent_id,
        "sort_order": page.sort_order,
        "page_type": page.page_type,
        "created_at": page.created_at,
        "updated_at": page.updated_at,
    }


def _block_dict(block):
    return {
        "id": block.id,
        "page_id": block.page_id,
        "block_type": block.block_type,
        "content_markdown": block.content_markdown,
        "sort_order": block.sort_order,
    }


def _task_dict(task):
    return {
        "id": task.id,
        "content_block_id": task.content_block_id,
        "text": task.text,
        "is_checked": task.is_checked,
        "recurrence_type": task.recurrence_type,
        "due_date": task.due_date,
        "parent_task_id": task.parent_task_id,
        "sort_order": task.sort_order,
    }


class UndoManager:
    def __init__(self):
        self._actions = []

    def push(self, action: dict):
        self._prune()
        action["timestamp"] = datetime.now()
        self._actions.append(action)

    def pop(self) -> dict | None:
        self._prune()
        if not self._actions:
            return None
        action = self._actions.pop()
        self._restore(action)
        return action

    def can_undo(self) -> bool:
        self._prune()
        return bool(self._actions)

    def _prune(self):
        cutoff = datetime.now() - UNDO_DURATION
        self._actions = [a for a in self._actions if a["timestamp"] > cutoff]

    def _restore(self, action):
        conn = get_connection()
        try:
            if action["type"] == "page":
                self._restore_page(conn, action)
            elif action["type"] == "block":
                self._restore_block(conn, action)
            elif action["type"] == "task":
                self._restore_task(conn, action)
            elif action["type"] == "bulk":
                for sub in action["actions"]:
                    if sub["type"] == "page":
                        self._restore_page(conn, sub)
            conn.commit()
        finally:
            conn.close()

    def _restore_page(self, conn, action):
        p = action["page"]
        conn.execute(
            """INSERT INTO pages (id, title, parent_id, sort_order,
            page_type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?,
            COALESCE(?, datetime('now')), COALESCE(?, datetime('now')))""",
            (
                p["id"],
                p["title"],
                p.get("parent_id"),
                p.get("sort_order", 0),
                p.get("page_type", "page"),
                p.get("created_at"),
                p.get("updated_at"),
            ),
        )
        for b in action["blocks"]:
            conn.execute(
                "INSERT INTO content_blocks (id, page_id, block_type,"
                " content_markdown, sort_order)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    b["id"],
                    b["page_id"],
                    b.get("block_type", "text"),
                    b.get("content_markdown", ""),
                    b.get("sort_order", 0),
                ),
            )
        for t in action["tasks"]:
            conn.execute(
                "INSERT INTO tasks (id, content_block_id, text,"
                " is_checked, recurrence_type, due_date,"
                " parent_task_id, sort_order)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    t["id"],
                    t["content_block_id"],
                    t.get("text", ""),
                    int(t.get("is_checked", False)),
                    t.get("recurrence_type", "none"),
                    t.get("due_date"),
                    t.get("parent_task_id"),
                    t.get("sort_order", 0),
                ),
            )
        for child in action.get("children", []):
            self._restore_page(conn, child)

    def _restore_block(self, conn, action):
        b = action["block"]
        conn.execute(
            "INSERT INTO content_blocks (id, page_id, block_type,"
            " content_markdown, sort_order)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                b["id"],
                b["page_id"],
                b.get("block_type", "text"),
                b.get("content_markdown", ""),
                b.get("sort_order", 0),
            ),
        )
        for t in action["tasks"]:
            conn.execute(
                "INSERT INTO tasks (id, content_block_id, text,"
                " is_checked, recurrence_type, due_date,"
                " parent_task_id, sort_order)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    t["id"],
                    t["content_block_id"],
                    t.get("text", ""),
                    int(t.get("is_checked", False)),
                    t.get("recurrence_type", "none"),
                    t.get("due_date"),
                    t.get("parent_task_id"),
                    t.get("sort_order", 0),
                ),
            )

    def _restore_task(self, conn, action):
        t = action["task"]
        conn.execute(
            "INSERT INTO tasks (id, content_block_id, text,"
            " is_checked, recurrence_type, due_date,"
            " parent_task_id, sort_order)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                t["id"],
                t["content_block_id"],
                t.get("text", ""),
                int(t.get("is_checked", False)),
                t.get("recurrence_type", "none"),
                t.get("due_date"),
                t.get("parent_task_id"),
                t.get("sort_order", 0),
            ),
        )


undo_manager = UndoManager()
