from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterable, List, Mapping, MutableMapping, Sequence

Example = MutableMapping[str, object]


@dataclass
class ReplayMemory:
    capacity: int
    seed: int = 0
    items: List[Example] = field(default_factory=list)
    seen: int = 0

    def __post_init__(self) -> None:
        if self.capacity < 0:
            raise ValueError("capacity must be non-negative")
        self._rng = random.Random(self.seed)

    def add(self, example: Mapping[str, object]) -> None:
        self.seen += 1
        if self.capacity == 0:
            return
        item = dict(example)
        if len(self.items) < self.capacity:
            self.items.append(item)
            return
        replace_index = self._rng.randrange(self.seen)
        if replace_index < self.capacity:
            self.items[replace_index] = item

    def add_many(self, examples: Iterable[Mapping[str, object]]) -> None:
        for example in examples:
            self.add(example)

    def candidates(self, candidate_count: int) -> List[Example]:
        if candidate_count < 0:
            raise ValueError("candidate_count must be non-negative")
        if candidate_count >= len(self.items):
            return [dict(item) for item in self.items]
        indexes = sorted(self._rng.sample(range(len(self.items)), candidate_count))
        return [dict(self.items[index]) for index in indexes]


def make_stream(tasks: Sequence[Sequence[tuple[Sequence[float], int]]]) -> List[Example]:
    stream: List[Example] = []
    for task_id, task_items in enumerate(tasks):
        for local_index, (features, label) in enumerate(task_items):
            stream.append({
                "example_id": f"t{task_id}_{local_index}",
                "task_id": task_id,
                "features": [float(value) for value in features],
                "label": int(label),
            })
    return stream


def compute_forgetting(accuracy_history: Mapping[str, Sequence[float]]) -> dict:
    per_task = {}
    forgetting_values = []
    for task_id, values in accuracy_history.items():
        if not values:
            continue
        best = max(float(value) for value in values)
        final = float(values[-1])
        forgetting = max(0.0, best - final)
        per_task[str(task_id)] = {"best": best, "final": final, "forgetting": forgetting}
        forgetting_values.append(forgetting)
    average = sum(forgetting_values) / len(forgetting_values) if forgetting_values else 0.0
    return {"average_forgetting": average, "per_task": per_task}
