#!/usr/bin/env python3
"""Tiny Ray Data pipeline smoke helper.

The default invocation prints help through argparse and does not import Ray. Pass
--run to execute a small in-memory Ray Data pipeline with no network access.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a tiny Ray Data from_items -> map_batches -> take pipeline. "
            "No network or external files are used."
        )
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute the tiny in-memory Ray Data pipeline. Without this flag, only argument parsing is exercised.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=6,
        help="Number of synthetic rows to generate for the smoke run.",
    )
    parser.add_argument(
        "--num-blocks",
        type=int,
        default=2,
        help="Requested initial Ray Data blocks via override_num_blocks.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=3,
        help="Batch size for map_batches during the smoke run.",
    )
    parser.add_argument(
        "--write-parquet",
        action="store_true",
        help="Also write the tiny result to a temporary or user-provided Parquet directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory for --write-parquet. If omitted, a temporary directory is used and removed.",
    )
    parser.add_argument(
        "--keep-temp-output",
        action="store_true",
        help="Keep the auto-created temporary Parquet directory instead of removing it.",
    )
    parser.add_argument(
        "--num-cpus",
        type=int,
        default=2,
        help="Number of local CPU slots requested from ray.init for the smoke run.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.rows < 1:
        raise SystemExit("--rows must be >= 1")
    if args.num_blocks < 1:
        raise SystemExit("--num-blocks must be >= 1")
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be >= 1")
    if args.num_cpus < 1:
        raise SystemExit("--num-cpus must be >= 1")
    if args.output_dir is not None and not args.write_parquet:
        raise SystemExit("--output-dir requires --write-parquet")
    if args.keep_temp_output and args.output_dir is not None:
        raise SystemExit("--keep-temp-output only applies when --output-dir is omitted")


def enrich_batch(batch: Dict[str, Any]) -> Dict[str, Any]:
    values = batch["value"]
    return {
        "id": batch["id"],
        "value": values,
        "double_value": values * 2,
        "bucket": values % 2,
    }


def run_smoke(args: argparse.Namespace) -> Dict[str, Any]:
    try:
        import ray
    except ModuleNotFoundError as exc:
        if exc.name == "ray":
            raise SystemExit(
                "Ray is not importable. Install the narrow data extra first, for example: pip install 'ray[data]'."
            ) from exc
        raise

    ray.init(num_cpus=args.num_cpus, include_dashboard=False, ignore_reinit_error=True)
    try:
        rows = [{"id": idx, "value": idx + 1} for idx in range(args.rows)]
        dataset = ray.data.from_items(rows, override_num_blocks=args.num_blocks)
        transformed = dataset.map_batches(
            enrich_batch,
            batch_format="numpy",
            batch_size=args.batch_size,
        )
        preview = transformed.take(min(args.rows, 5))
        materialized = transformed.materialize()
        summary: Dict[str, Any] = {
            "rows_requested": args.rows,
            "num_blocks_requested": args.num_blocks,
            "batch_size": args.batch_size,
            "preview": preview,
            "schema": str(materialized.schema()),
            "stats_available": bool(materialized.stats()),
        }

        if args.write_parquet:
            temp_dir = None
            if args.output_dir is None:
                temp_dir = Path(tempfile.mkdtemp(prefix="ray-data-smoke-"))
                output_dir = temp_dir / "parquet"
            else:
                output_dir = args.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            materialized.write_parquet(str(output_dir), mode="overwrite")
            roundtrip_count = ray.data.read_parquet(str(output_dir)).count()
            summary["parquet_rows"] = roundtrip_count
            summary["parquet_output"] = str(output_dir)
            if temp_dir is not None and not args.keep_temp_output:
                shutil.rmtree(temp_dir)
                summary["parquet_output_removed"] = True
        return summary
    finally:
        ray.shutdown()


def main() -> None:
    args = parse_args()
    validate_args(args)
    if not args.run:
        print("Argument parsing succeeded. Pass --run to execute the Ray Data smoke pipeline.")
        return
    print(json.dumps(run_smoke(args), indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
