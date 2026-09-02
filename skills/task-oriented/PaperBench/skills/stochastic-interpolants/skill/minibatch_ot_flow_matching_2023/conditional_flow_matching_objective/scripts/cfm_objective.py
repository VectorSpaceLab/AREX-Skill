from __future__ import annotations

import json
from typing import Iterable, List, Sequence

Point = List[float]


def _as_points(values: Sequence[Sequence[float]]) -> list[Point]:
    points = [[float(v) for v in row] for row in values]
    if not points or not points[0]:
        raise ValueError("points must be a non-empty 2D array")
    width = len(points[0])
    if any(len(row) != width for row in points):
        raise ValueError("all points must have the same dimension")
    return points


def _times(times: float | Sequence[float], n: int) -> list[float]:
    if isinstance(times, (int, float)):
        out = [float(times)] * n
    else:
        out = [float(t) for t in times]
    if len(out) != n:
        raise ValueError("time count must match batch size")
    if any(t < 0.0 or t > 1.0 for t in out):
        raise ValueError("times must lie in [0, 1]")
    return out


def interpolate(source: Sequence[Sequence[float]], target: Sequence[Sequence[float]], times: float | Sequence[float]) -> dict:
    x0 = _as_points(source)
    x1 = _as_points(target)
    if len(x0) != len(x1) or len(x0[0]) != len(x1[0]):
        raise ValueError("source and target shapes must match")
    ts = _times(times, len(x0))
    xt = []
    velocities = []
    for row0, row1, t in zip(x0, x1, ts):
        xt.append([(1.0 - t) * a + t * b for a, b in zip(row0, row1)])
        velocities.append([b - a for a, b in zip(row0, row1)])
    return {"x_t": xt, "target_velocity": velocities, "times": ts}


def mean_squared_velocity_loss(predictions: Sequence[Sequence[float]], targets: Sequence[Sequence[float]]) -> dict:
    pred = _as_points(predictions)
    tgt = _as_points(targets)
    if len(pred) != len(tgt) or len(pred[0]) != len(tgt[0]):
        raise ValueError("prediction and target shapes must match")
    per_sample = []
    for row_pred, row_tgt in zip(pred, tgt):
        per_sample.append(sum((p - u) ** 2 for p, u in zip(row_pred, row_tgt)) / len(row_pred))
    return {"loss": sum(per_sample) / len(per_sample), "per_sample_loss": per_sample}


def build_training_batch(source, target, times, predictions=None) -> dict:
    batch = interpolate(source, target, times)
    if predictions is not None:
        batch.update(mean_squared_velocity_loss(predictions, batch["target_velocity"]))
    return batch


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    args = parser.parse_args()
    payload = json.load(open(args.input_json, "r", encoding="utf-8"))
    print(json.dumps(build_training_batch(payload["source"], payload["target"], payload["times"], payload.get("predictions")), indent=2))
