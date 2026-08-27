#!/usr/bin/env python3
"""Run tiny River stream ingestion, delayed-label, and sample-weight checks."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test River stream and evaluation APIs.")
    parser.add_argument("--rows", type=int, default=6, help="Rows to place in the temporary CSV fixture.")
    parser.add_argument("--delay-minutes", type=int, default=2, help="Delayed-label reveal delay.")
    return parser.parse_args()


def write_csv_fixture(path: Path, rows: int) -> None:
    start = dt.datetime(2024, 1, 1, 12, 0)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["moment", "f1", "f2", "label"])
        for i in range(rows):
            moment = start + dt.timedelta(minutes=i)
            writer.writerow([moment.isoformat(timespec="seconds"), float(i), float(rows - i), int(i % 2)])


def csv_rows(path: Path):
    from river import stream

    return list(
        stream.iter_csv(
            path,
            target="label",
            converters={"f1": float, "f2": float, "label": int},
            parse_dates={"moment": "%Y-%m-%dT%H:%M:%S"},
        )
    )


def check_csv(rows: list[tuple[dict, int]]) -> None:
    if not rows:
        raise AssertionError("iter_csv yielded no rows")
    x0, y0 = rows[0]
    if set(x0) != {"moment", "f1", "f2"}:
        raise AssertionError(f"unexpected feature keys: {sorted(x0)}")
    if type(x0["moment"]) is not dt.datetime:
        raise AssertionError("moment was not parsed as datetime")
    if type(y0) is not int:
        raise AssertionError("label was not parsed as int")


def check_progressive_validation(rows: list[tuple[dict, int]], delay_minutes: int) -> None:
    from river import base, evaluate, metrics, stream

    class WeightedMajorityClassifier(base.Classifier):
        def __init__(self) -> None:
            self.class_weight = {0: 0.0, 1: 0.0}
            self.weights_seen: list[float] = []

        def predict_proba_one(self, x, **kwargs):
            total = self.class_weight[0] + self.class_weight[1]
            if total == 0.0:
                return {0: 0.5, 1: 0.5}
            return {0: self.class_weight[0] / total, 1: self.class_weight[1] / total}

        def learn_one(self, x, y, w=1.0):
            self.weights_seen.append(w)
            self.class_weight[y] += w

    events = list(stream.simulate_qa(rows, moment="moment", delay=dt.timedelta(minutes=delay_minutes)))
    if len(events) != 2 * len(rows):
        raise AssertionError("simulate_qa did not emit question and answer events for every row")

    model = WeightedMajorityClassifier()
    metric = evaluate.progressive_val_score(
        dataset=rows,
        model=model,
        metric=metrics.Accuracy(),
        moment="moment",
        delay=dt.timedelta(minutes=delay_minutes),
    )
    if not 0.0 <= metric.get() <= 1.0:
        raise AssertionError("delayed progressive validation returned an invalid accuracy")
    if len(model.weights_seen) != len(rows):
        raise AssertionError("delayed learning did not reach every sample once")

    weighted_rows = [({"f": 0.0}, 0, {"w": 1.0}), ({"f": 1.0}, 1, {"w": 2.0}), ({"f": 2.0}, 1, {"w": 4.0})]
    weighted = WeightedMajorityClassifier()
    evaluate.progressive_val_score(dataset=weighted_rows, model=weighted, metric=metrics.Accuracy())
    if weighted.weights_seen != [1.0, 2.0, 4.0]:
        raise AssertionError("sample weights were not forwarded to learn_one")


def main() -> int:
    args = parse_args()
    if args.delay_minutes < 1:
        raise SystemExit("--delay-minutes must be at least 1")
    if args.rows <= args.delay_minutes:
        raise SystemExit("--rows must be greater than --delay-minutes")

    with tempfile.TemporaryDirectory() as tmp_dir:
        fixture = Path(tmp_dir) / "stream_fixture.csv"
        write_csv_fixture(fixture, args.rows)
        rows = csv_rows(fixture)
        check_csv(rows)
        check_progressive_validation(rows, args.delay_minutes)

    print("stream_evaluation_smoke_ok=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
