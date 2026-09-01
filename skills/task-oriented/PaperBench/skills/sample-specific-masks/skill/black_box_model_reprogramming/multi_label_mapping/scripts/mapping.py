#!/usr/bin/env python3
"""Multi-label mapping utilities for BAR."""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence


def normalize_rows(rows: Sequence[Sequence[float]]) -> List[List[float]]:
    out = []
    for row in rows:
        vals = [max(0.0, float(x)) for x in row]
        total = sum(vals)
        if total <= 0:
            vals = [1.0 / len(vals) for _ in vals]
        else:
            vals = [x / total for x in vals]
        out.append(vals)
    return out


def apply_mapping(source_probs: Sequence[Sequence[float]], mapping: Dict[int, Sequence[int]], renormalize: bool = True) -> List[List[float]]:
    rows = normalize_rows(source_probs)
    targets = sorted(mapping)
    result = []
    used = []
    for target in targets:
        group = list(mapping[target])
        if not group:
            raise ValueError("mapping groups must be non-empty")
        used.extend(group)
    if len(set(used)) != len(used):
        raise ValueError("source labels may not overlap across target groups")
    for row in rows:
        mapped = []
        for target in targets:
            group = list(mapping[target])
            if max(group) >= len(row) or min(group) < 0:
                raise ValueError("source label index out of range")
            mapped.append(sum(row[i] for i in group) / len(group))
        if renormalize:
            total = sum(mapped)
            mapped = [x / total for x in mapped] if total > 0 else [1.0 / len(mapped) for _ in mapped]
        result.append(mapped)
    return result


def frequency_mapping(initial_probs: Sequence[Sequence[float]], labels: Sequence[int], group_size: int, target_count: int | None = None) -> Dict[int, List[int]]:
    rows = normalize_rows(initial_probs)
    if len(rows) != len(labels):
        raise ValueError("initial_probs and labels length mismatch")
    if group_size < 1:
        raise ValueError("group_size must be positive")
    label_values = sorted(set(int(y) for y in labels)) if target_count is None else list(range(target_count))
    source_count = len(rows[0])
    if len(label_values) * group_size > source_count:
        raise ValueError("not enough source labels for non-overlapping mapping")
    used = set()
    mapping: Dict[int, List[int]] = {}
    for target in label_values:
        class_rows = [row for row, y in zip(rows, labels) if int(y) == target]
        if not class_rows:
            raise ValueError(f"no samples for target label {target}")
        means = [(sum(row[j] for row in class_rows) / len(class_rows), j) for j in range(source_count) if j not in used]
        means.sort(key=lambda x: (-x[0], x[1]))
        chosen = [j for _, j in means[:group_size]]
        mapping[int(target)] = chosen
        used.update(chosen)
    return mapping
