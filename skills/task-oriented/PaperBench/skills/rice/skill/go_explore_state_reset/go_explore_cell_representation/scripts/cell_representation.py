from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple


def encode_cell(state: Dict[str, Any], fields: Iterable[str] | None = None, bucket_size: int = 1) -> Tuple[Any, ...]:
    if fields is not None:
        key = []
        for field in fields:
            if field not in state:
                raise KeyError(f"missing field for cell encoding: {field}")
            key.append(state[field])
        return tuple(key)
    if "x" not in state or "y" not in state:
        raise KeyError("coordinate encoding requires x and y")
    if bucket_size <= 0:
        raise ValueError("bucket_size must be positive")
    room = state.get("room", 0)
    return (room, int(state["x"]) // bucket_size, int(state["y"]) // bucket_size)


def describe_cell_config(fields: Iterable[str] | None = None, bucket_size: int = 1) -> Dict[str, Any]:
    if fields is not None:
        return {"mode": "domain_fields", "fields": list(fields)}
    return {"mode": "coordinate_bucket", "bucket_size": bucket_size}
