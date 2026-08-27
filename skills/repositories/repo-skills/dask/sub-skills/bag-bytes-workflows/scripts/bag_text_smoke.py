#!/usr/bin/env python
"""Smoke-check Dask Bag text, JSON, foldby, and dataframe conversion."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any


def _write_fixture(root: Path) -> str:
    rows_by_file = {
        "events-0.jsonl": [
            {"user": "alice", "status": "ok", "amount": 10},
            {"user": "bob", "status": "ok", "amount": 5},
            "{malformed-json",
        ],
        "events-1.jsonl": [
            {"user": "alice", "status": "warn", "amount": 2},
            {"user": "carol", "amount": 7},
        ],
    }
    for filename, rows in rows_by_file.items():
        path = root / filename
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                if isinstance(row, str):
                    handle.write(row + "\n")
                else:
                    handle.write(json.dumps(row, sort_keys=True) + "\n")
    return str(root / "events-*.jsonl")


def _parse_line(item: tuple[str, str]) -> dict[str, Any]:
    line, path = item
    try:
        record = json.loads(line)
    except json.JSONDecodeError as exc:
        return {
            "valid": False,
            "path": Path(path).name,
            "error": exc.msg,
            "raw": line.rstrip("\n"),
        }
    return {"valid": True, "path": Path(path).name, "record": record}


def _add_amount(total: float, record: dict[str, Any]) -> float:
    return total + float(record.get("amount", 0) or 0)


def run_smoke(files_per_partition: int, scheduler: str) -> dict[str, Any]:
    try:
        import dask.bag as db
    except ImportError as exc:
        raise SystemExit(
            "This smoke check requires Dask to be installed in the active Python environment."
        ) from exc

    with tempfile.TemporaryDirectory(prefix="dask-bag-smoke-") as tmp:
        pattern = _write_fixture(Path(tmp))
        parsed = db.read_text(
            pattern,
            files_per_partition=files_per_partition,
            include_path=True,
        ).map(_parse_line)

        good = parsed.filter(lambda row: row["valid"]).pluck("record")
        bad = parsed.remove(lambda row: row["valid"])

        status_counts = dict(
            good.pluck("status", default="missing")
            .frequencies(sort=True)
            .compute(scheduler=scheduler)
        )
        amount_by_user = dict(
            good.foldby(
                key="user",
                binop=_add_amount,
                initial=0.0,
                combine=lambda left, right: left + right,
                combine_initial=0.0,
            ).compute(scheduler=scheduler)
        )

        meta = {"user": "object", "status": "object", "amount": "float64"}
        dataframe = good.map(
            lambda record: {
                "user": record.get("user"),
                "status": record.get("status", "missing"),
                "amount": float(record.get("amount", 0) or 0),
            }
        ).to_dataframe(meta=meta)

        return {
            "record_count": good.count().compute(scheduler=scheduler),
            "bad_count": bad.count().compute(scheduler=scheduler),
            "status_counts": status_counts,
            "amount_by_user": amount_by_user,
            "dataframe_columns": list(dataframe.columns),
            "dataframe_rows": len(dataframe.compute(scheduler=scheduler)),
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create a temporary JSON-lines fixture and smoke-check Dask Bag "
            "read_text, malformed-row handling, frequencies, foldby, and "
            "to_dataframe(meta=...)."
        )
    )
    parser.add_argument(
        "--files-per-partition",
        type=int,
        default=2,
        help="Number of small text files to group into each bag partition.",
    )
    parser.add_argument(
        "--scheduler",
        default="sync",
        choices=["sync", "synchronous", "threads", "processes", "single-threaded"],
        help="Scheduler to use for the tiny local smoke computation.",
    )
    args = parser.parse_args()

    result = run_smoke(args.files_per_partition, args.scheduler)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
