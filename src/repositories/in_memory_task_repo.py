from src.models.task import Task


class InMemoryTaskRepo:
    def __init__(self):
        self._tasks = []
        self._next_id = 0

    def get_by_block(self, block_id: int) -> list[Task]:
        return [t for t in self._tasks if t.content_block_id == block_id]

    def create(self, task: Task) -> int:
        tid = self._next_id
        self._next_id += 1
        task.id = tid
        siblings = [
            t for t in self._tasks if t.content_block_id == task.content_block_id
        ]
        task.sort_order = max((t.sort_order for t in siblings), default=-1) + 1
        self._tasks.append(task)
        return tid

    def update(self, task: Task):
        for t in self._tasks:
            if t.id == task.id:
                t.text = task.text
                t.is_checked = task.is_checked
                t.recurrence_type = task.recurrence_type
                t.due_date = task.due_date
                t.sort_order = task.sort_order
                return

    def delete(self, task_id: int):
        self._tasks[:] = [t for t in self._tasks if t.id != task_id]

    def delete_by_block(self, block_id: int):
        self._tasks[:] = [t for t in self._tasks if t.content_block_id != block_id]
