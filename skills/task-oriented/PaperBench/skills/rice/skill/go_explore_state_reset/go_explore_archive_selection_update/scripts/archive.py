from __future__ import annotations

import random
from typing import Any, Dict, Hashable, Tuple

Archive = Dict[Hashable, Dict[str, Any]]


def trajectory_length(record: Dict[str, Any]) -> int:
    return int(record.get("length", len(record.get("actions", []))))


def should_replace(old: Dict[str, Any], new: Dict[str, Any]) -> bool:
    if new["score"] > old["score"]:
        return True
    return new["score"] == old["score"] and trajectory_length(new) < trajectory_length(old)


def update_archive(archive: Archive, record: Dict[str, Any]) -> bool:
    key = tuple(record["cell_key"])
    candidate = dict(record)
    candidate["cell_key"] = key
    candidate["length"] = trajectory_length(candidate)
    candidate.setdefault("update_count", 0)
    candidate.setdefault("selection_count", 0)
    if key not in archive:
        candidate["update_count"] = 1
        archive[key] = candidate
        return True
    if should_replace(archive[key], candidate):
        candidate["update_count"] = int(archive[key].get("update_count", 0)) + 1
        candidate["selection_count"] = int(archive[key].get("selection_count", 0))
        archive[key] = candidate
        return True
    return False


def select_cell(archive: Archive, seed: int = 0) -> Tuple[Hashable, Dict[str, Any]]:
    if not archive:
        raise ValueError("cannot select from an empty archive")
    keys = sorted(archive.keys(), key=repr)
    weights = []
    for key in keys:
        entry = archive[key]
        weights.append((1.0 + max(0.0, float(entry.get("score", 0)))) / (1.0 + float(entry.get("selection_count", 0))))
    rng = random.Random(seed)
    selected = rng.choices(keys, weights=weights, k=1)[0]
    archive[selected]["selection_count"] = int(archive[selected].get("selection_count", 0)) + 1
    return selected, archive[selected]
