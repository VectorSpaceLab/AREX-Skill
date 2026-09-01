from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

Vector = List[float]
Pair = Tuple[Vector, Vector]

def dot(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("vectors must have matching dimensions")
    return sum(x * y for x, y in zip(a, b))

def subtract(a: Sequence[float], b: Sequence[float]) -> Vector:
    if len(a) != len(b):
        raise ValueError("vectors must have matching dimensions")
    return [x - y for x, y in zip(a, b)]

def update_memory(memory: Iterable[Pair], x_old: Sequence[float], x_new: Sequence[float], g_old: Sequence[float], g_new: Sequence[float], m: int, tolerance: float = 1e-12) -> List[Pair]:
    if m < 1:
        raise ValueError("memory limit m must be positive")
    s = subtract(x_new, x_old)
    y = subtract(g_new, g_old)
    new_memory = [(list(si), list(yi)) for si, yi in memory]
    if dot(s, y) > tolerance:
        new_memory.append((s, y))
    return new_memory[-m:]
