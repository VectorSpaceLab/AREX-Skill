#!/usr/bin/env python3
"""Inspect Roboflow Inference workflow CLI JSON inputs and output folders.

This helper is intentionally lightweight and depends only on the Python standard
library. It does not run a Workflow and does not import Roboflow packages; use it
to catch malformed JSON parameter/spec files or to summarize files produced by
`inference workflows process-image`, `process-images-directory`, or
`process-video`.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterable


def load_json(path: Path, expect_object: bool, label: str) -> int:
    if not path.is_file():
        print(f"ERROR: {label} does not exist or is not a file: {path}")
        return 1
    try:
        with path.open("r", encoding="utf-8") as f:
            value: Any = json.load(f)
    except Exception as error:  # noqa: BLE001 - print user-facing parse cause
        print(f"ERROR: {label} is not valid JSON: {path}: {error}")
        return 1
    if expect_object and not isinstance(value, dict):
        print(f"ERROR: {label} must be a JSON object for Workflow parameters: {path}")
        return 1
    kind = type(value).__name__
    keys = f" keys={sorted(value.keys())}" if isinstance(value, dict) else ""
    print(f"OK: {label} JSON parsed ({kind}){keys}: {path}")
    return 0


def non_empty_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def iter_result_jsons(output_dir: Path) -> Iterable[Path]:
    yield from sorted(output_dir.glob("*/results.json"))


def inspect_image_like(output_dir: Path, expect_aggregation: str) -> int:
    status = 0
    progress = output_dir / "progress.log"
    processed = non_empty_lines(progress)
    result_jsons = list(iter_result_jsons(output_dir))
    print(f"progress.log: {'present' if progress.exists() else 'missing'} processed_entries={len(processed)}")
    print(f"per-image results.json files: {len(result_jsons)}")
    for result in result_jsons[:10]:
        image_outputs = [p for p in result.parent.rglob("*.jpg")]
        print(f"  - {result.parent.name}: results.json, jpg_outputs={len(image_outputs)}")
    if len(result_jsons) > 10:
        print(f"  ... {len(result_jsons) - 10} more result directories")
    if not result_jsons:
        print("WARN: no <image>/results.json files found")
        status = max(status, 1)

    csv_path = output_dir / "aggregated_results.csv"
    jsonl_path = output_dir / "aggregated_results.jsonl"
    if expect_aggregation != "none":
        expected = csv_path if expect_aggregation == "csv" else jsonl_path
        if expected.is_file():
            print(f"OK: expected aggregate exists: {expected.name}")
        else:
            print(f"ERROR: expected aggregate missing: {expected.name}")
            status = 1
    else:
        print("aggregation expectation: none")

    if csv_path.is_file():
        try:
            with csv_path.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            print(f"aggregate CSV rows={len(rows)} columns={rows[0].keys() if rows else []}")
        except Exception as error:  # noqa: BLE001
            print(f"WARN: could not read aggregate CSV: {error}")
    if jsonl_path.is_file():
        lines = non_empty_lines(jsonl_path)
        print(f"aggregate JSONL records={len(lines)}")

    for failure_file in sorted(output_dir.glob("failed_files_processing_*.jsonl")):
        print(f"failure report: {failure_file.name} records={len(non_empty_lines(failure_file))}")
    return status


def inspect_video(output_dir: Path, output_file_type: str | None) -> int:
    status = 0
    result_files = sorted(output_dir.glob("workflow_results_source_*.csv")) + sorted(
        output_dir.glob("workflow_results_source_*.jsonl")
    )
    preview_files = sorted(output_dir.glob("source_*_output_*_preview.mp4"))
    print(f"video structured result files: {len(result_files)}")
    for path in result_files:
        print(f"  - {path.name}")
    print(f"video preview files: {len(preview_files)}")
    for path in preview_files:
        print(f"  - {path.name}")
    if output_file_type:
        expected = output_dir / f"workflow_results_source_0.{output_file_type}"
        if expected.is_file():
            print(f"OK: expected video structured file exists: {expected.name}")
        else:
            print(f"ERROR: expected video structured file missing: {expected.name}")
            status = 1
    elif not result_files:
        print("WARN: no workflow_results_source_* structured files found")
        status = 1
    return status


def detect_mode(output_dir: Path) -> str:
    if any(output_dir.glob("workflow_results_source_*.csv")) or any(
        output_dir.glob("workflow_results_source_*.jsonl")
    ) or any(output_dir.glob("source_*_output_*_preview.mp4")):
        return "video"
    return "image-like"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow-spec", type=Path, help="Optional Workflow specification JSON to validate.")
    parser.add_argument(
        "--params-json",
        type=Path,
        action="append",
        default=[],
        help="Optional Workflow parameters JSON object to validate; can be repeated.",
    )
    parser.add_argument("--output-dir", type=Path, help="Output directory to inspect.")
    parser.add_argument(
        "--mode",
        choices=["auto", "image", "images-directory", "video"],
        default="auto",
        help="Expected output mode. 'image' and 'images-directory' share the same per-image layout.",
    )
    parser.add_argument(
        "--expect-aggregation",
        choices=["csv", "jsonl", "none"],
        default="none",
        help="Expected image-directory aggregate file.",
    )
    parser.add_argument(
        "--expect-video-type",
        choices=["csv", "jsonl"],
        help="Expected process-video structured result extension.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    status = 0
    if args.workflow_spec is not None:
        status = max(status, load_json(args.workflow_spec, expect_object=False, label="workflow spec"))
    for params_path in args.params_json:
        status = max(status, load_json(params_path, expect_object=True, label="workflow params"))

    if args.output_dir is None:
        return status
    if not args.output_dir.is_dir():
        print(f"ERROR: output directory does not exist or is not a directory: {args.output_dir}")
        return 1

    mode = args.mode
    if mode == "auto":
        detected = detect_mode(args.output_dir)
        print(f"detected output mode: {detected}")
        mode = "video" if detected == "video" else "images-directory"
    if mode in {"image", "images-directory"}:
        status = max(status, inspect_image_like(args.output_dir, args.expect_aggregation))
    elif mode == "video":
        status = max(status, inspect_video(args.output_dir, args.expect_video_type))
    return status


if __name__ == "__main__":
    sys.exit(main())
