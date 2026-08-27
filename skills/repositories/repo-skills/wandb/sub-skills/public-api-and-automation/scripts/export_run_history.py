#!/usr/bin/env python3
"""Export W&B run history through the public wandb.Api."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import wandb


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export unsampled W&B run history to CSV or JSONL.",
        allow_abbrev=False,
    )
    parser.add_argument("--entity", required=True, help="W&B entity or team name.")
    parser.add_argument("--project", required=True, help="W&B project name.")
    parser.add_argument("--run", required=True, help="Run ID within the project.")
    parser.add_argument("--out", required=True, help="Output CSV or JSONL path.")
    parser.add_argument(
        "--format",
        choices=("csv", "jsonl"),
        default=None,
        help="Output format. Defaults from --out suffix, then jsonl.",
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        default=None,
        help="Metric keys to export. Omit to export all history keys.",
    )
    parser.add_argument("--min-step", type=int, default=0, help="Inclusive minimum step.")
    parser.add_argument("--max-step", type=int, default=None, help="Exclusive maximum step.")
    parser.add_argument(
        "--page-size",
        type=int,
        default=1000,
        help="History rows requested per API page.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Stop after this many rows for bounded exports.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Public API request timeout in seconds.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Optional W&B server base URL for self-hosted or dedicated deployments.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve and describe the export without writing rows.",
    )
    return parser.parse_args()


def infer_format(path: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    if path.suffix.lower() == ".csv":
        return "csv"
    return "jsonl"


def build_api(timeout: int | None, base_url: str | None) -> "wandb.Api":
    import wandb

    overrides = {"base_url": base_url} if base_url else None
    return wandb.Api(overrides=overrides, timeout=timeout)


def iter_limited(rows: Iterable[dict[str, Any]], max_rows: int | None) -> Iterator[dict[str, Any]]:
    for index, row in enumerate(rows):
        if max_rows is not None and index >= max_rows:
            break
        yield row


def json_default(value: Any) -> str:
    return str(value)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, default=json_default, sort_keys=True) + "\n")
            count += 1
    return count


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    iterator = iter(rows)
    buffered: list[dict[str, Any]] = []
    fieldnames: list[str] = []

    for row in iterator:
        buffered.append(row)
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
        if len(buffered) >= 100:
            break

    if not buffered:
        path.write_text("", encoding="utf-8")
        return 0

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(buffered)
        count = len(buffered)

        for row in iterator:
            unknown_keys = [key for key in row if key not in fieldnames]
            if unknown_keys:
                raise ValueError(
                    "CSV export encountered new keys after writing the header: "
                    + ", ".join(sorted(unknown_keys))
                    + ". Re-run with --format jsonl or include explicit --keys."
                )
            writer.writerow(row)
            count += 1

    return count


def main() -> int:
    args = parse_args()
    out_path = Path(args.out)
    out_format = infer_format(out_path, args.format)
    run_path = f"{args.entity}/{args.project}/{args.run}"

    api = build_api(timeout=args.timeout, base_url=args.base_url)
    run = api.run(run_path)

    print(f"Resolved run: {run_path}", file=sys.stderr)
    print(f"Output: {out_path} ({out_format})", file=sys.stderr)
    print(f"Keys: {args.keys or 'all'}", file=sys.stderr)
    print(
        f"Step range: [{args.min_step}, {args.max_step if args.max_step is not None else 'end'})",
        file=sys.stderr,
    )
    if args.max_rows is not None:
        print(f"Row cap: {args.max_rows}", file=sys.stderr)

    if args.dry_run:
        print("Dry run complete; no rows written.", file=sys.stderr)
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = run.scan_history(
        keys=args.keys,
        page_size=args.page_size,
        min_step=args.min_step,
        max_step=args.max_step,
    )
    limited_rows = iter_limited(rows, args.max_rows)

    if out_format == "csv":
        written = write_csv(out_path, limited_rows)
    else:
        written = write_jsonl(out_path, limited_rows)

    print(f"Wrote {written} rows to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
