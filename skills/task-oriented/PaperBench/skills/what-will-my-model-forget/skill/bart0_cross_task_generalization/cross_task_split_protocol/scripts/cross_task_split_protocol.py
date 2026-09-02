from __future__ import annotations

from typing import Any


def make_split(tasks: list[dict[str, Any]], split_type: str, held_out: str) -> dict[str, Any]:
    if not tasks:
        raise ValueError("tasks must be non-empty")
    key_by_type = {
        "leave_one_task": "task_id",
        "leave_one_dataset": "dataset",
        "leave_one_category": "category",
    }
    if split_type not in key_by_type:
        raise ValueError(f"unsupported split_type: {split_type}")
    key = key_by_type[split_type]
    unseen = [str(task["task_id"]) for task in tasks if str(task.get(key)) == held_out]
    seen = [str(task["task_id"]) for task in tasks if str(task.get(key)) != held_out]
    if not seen or not unseen:
        raise ValueError("split must contain at least one seen and unseen task")
    if set(seen) & set(unseen):
        raise ValueError("seen and unseen tasks overlap")
    return {"split_type": split_type, "held_out": held_out, "seen_task_ids": seen, "unseen_task_ids": unseen}
