#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from typing import Iterable


def _columns(batch: list[list[float]]) -> list[list[float]]:
    if not batch:
        raise ValueError("batch must not be empty")
    width = len(batch[0])
    if width == 0:
        raise ValueError("vectors must not be empty")
    if any(len(row) != width for row in batch):
        raise ValueError("all vectors must have the same length")
    return [[row[index] for row in batch] for index in range(width)]


def batch_stats(batch: list[list[float]]) -> dict:
    cols = _columns(batch)
    count = len(batch)
    mean = [sum(col) / count for col in cols]
    var = [sum((value - mean[i]) ** 2 for value in col) / count for i, col in enumerate(cols)]
    return {"mean": mean, "var": var, "count": count}


def merge_stats(existing: dict | None, batch: list[list[float]]) -> dict:
    incoming = batch_stats(batch)
    if not existing or int(existing.get("count", 0)) == 0:
        return incoming
    count_a = int(existing["count"])
    count_b = incoming["count"]
    total = count_a + count_b
    mean_a = [float(x) for x in existing["mean"]]
    var_a = [float(x) for x in existing["var"]]
    mean_b = incoming["mean"]
    var_b = incoming["var"]
    mean = []
    var = []
    for ma, va, mb, vb in zip(mean_a, var_a, mean_b, var_b):
        delta = mb - ma
        merged_mean = ma + delta * count_b / total
        merged_m2 = va * count_a + vb * count_b + delta * delta * count_a * count_b / total
        mean.append(merged_mean)
        var.append(merged_m2 / total)
    return {"mean": mean, "var": var, "count": total}


def normalize(batch: list[list[float]], stats: dict, clip: float = 5.0, eps: float = 1e-8) -> list[list[float]]:
    _columns(batch)
    mean = [float(x) for x in stats["mean"]]
    var = [float(x) for x in stats["var"]]
    output = []
    for row in batch:
        normed = []
        for value, m, v in zip(row, mean, var):
            scaled = (float(value) - m) / math.sqrt(max(v, 0.0) + eps)
            normed.append(max(-clip, min(clip, scaled)))
        output.append(normed)
    return output


def normalize_with_update(batch: list[list[float]], existing: dict | None = None, clip: float = 5.0) -> dict:
    stats = merge_stats(existing, batch)
    return {"normalized": normalize(batch, stats, clip=clip), "stats": stats}


def _self_test() -> None:
    result = normalize_with_update([[0.0, 10.0], [2.0, 14.0]])
    assert result["stats"]["count"] == 2
    assert all(-5.0 <= value <= 5.0 for row in result["normalized"] for value in row)
    merged = normalize_with_update([[100.0, -100.0]], result["stats"])
    assert merged["stats"]["count"] == 3
    clipped = normalize([[1000.0, -1000.0]], result["stats"], clip=5.0)
    assert clipped == [[5.0, -5.0]]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return 0
    payload = json.loads(open(args.input_json, encoding="utf-8").read()) if args.input_json else json.load(__import__("sys").stdin)
    print(json.dumps(normalize_with_update(payload["batch"], payload.get("stats"), payload.get("clip", 5.0)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
