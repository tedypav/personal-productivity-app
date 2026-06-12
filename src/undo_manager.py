from datetime import datetime, timedelta

from src.database import get_connection

UNDO_DURATION = timedelta(minutes=15)


def capture_page_tree(page_id: int) -> dict | None:
    from src.repositories.page_repo import PageRepo

    page = PageRepo().get_by_id(page_id)
    if not page:
        return None

    return {
        "page": _page_dict(page),
        "children": _capture_children(page_id),
    }


def _capture_children(parent_id: int) -> list:
    from src.repositories.page_repo import PageRepo

    result = []
    for child in PageRepo().get_children(parent_id):
        if child.id is not None:
            result.append(
                {
                    "page": _page_dict(child),
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
        for child in action.get("children", []):
            self._restore_page(conn, child)


undo_manager = UndoManager()
