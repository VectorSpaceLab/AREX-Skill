#!/usr/bin/env python3
"""Dry-run-first PySpark template for img2dataset downloads.

This helper intentionally does not import pyspark or img2dataset unless
--run or --check-backends is requested.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from typing import Any, Dict


INPUT_FORMATS = [
    "txt",
    "txt.gz",
    "csv",
    "csv.gz",
    "tsv",
    "tsv.gz",
    "json",
    "json.gz",
    "jsonl",
    "jsonl.gz",
    "parquet",
]
OUTPUT_FORMATS = ["webdataset", "files", "parquet", "tfrecord", "dummy"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare or run an img2dataset PySpark download. The default is a "
            "dry run that prints the execution plan without importing Spark."
        )
    )
    parser.add_argument("--url-list", help="Input URL list/table path. Required with --run.")
    parser.add_argument("--output-folder", help="Output folder or fsspec URL. Required with --run.")
    parser.add_argument("--input-format", default="parquet", choices=INPUT_FORMATS)
    parser.add_argument("--url-col", default="url", help="URL column for table formats.")
    parser.add_argument("--caption-col", default=None, help="Optional caption column for table formats.")
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument(
        "--processes-count",
        type=int,
        default=1,
        help=(
            "Used by img2dataset and as the default local Spark core count when "
            "--master is not provided. For an existing cluster, executor cores "
            "are controlled by Spark configuration."
        ),
    )
    parser.add_argument("--thread-count", type=int, default=32)
    parser.add_argument(
        "--subjob-size",
        type=int,
        default=1000,
        help="Number of reader shards submitted in one PySpark batch.",
    )
    parser.add_argument(
        "--master",
        default=None,
        help="Spark master URL such as local[16] or spark://master-node:7077. Defaults to local[processes_count].",
    )
    parser.add_argument("--driver-memory", default="16G", help="Spark driver memory for the template-created session.")
    parser.add_argument("--output-format", default="webdataset", choices=OUTPUT_FORMATS)
    parser.add_argument("--number-sample-per-shard", type=int, default=10000)
    parser.add_argument("--max-shard-retry", type=int, default=1)
    parser.add_argument("--retries", type=int, default=0, help="Per-image downloader retries; shard retry is --max-shard-retry.")
    parser.add_argument("--enable-wandb", action="store_true", help="Enable W&B logging.")
    parser.add_argument("--wandb-project", default="img2dataset")
    parser.add_argument(
        "--check-backends",
        action="store_true",
        help="Import pyspark/img2dataset and check Java before printing or running the plan.",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=True,
        help="Print the plan without importing Spark/img2dataset. This is the default.",
    )
    parser.add_argument(
        "--run",
        dest="dry_run",
        action="store_false",
        help="Execute the download. Requires --url-list and --output-folder.",
    )
    return parser


def package_version(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def check_backends() -> Dict[str, Any]:
    """Import required runtime modules and check Java without running downloads."""
    report: Dict[str, Any] = {"ok": True, "modules": {}, "java": {}}
    for module_name, distribution in [("pyspark", "pyspark"), ("img2dataset", "img2dataset")]:
        result: Dict[str, Any] = {"version": package_version(distribution)}
        try:
            module = importlib.import_module(module_name)
            result["import"] = "ok"
            result["module_version"] = getattr(module, "__version__", None)
        except Exception as exc:  # pylint: disable=broad-except
            result["import"] = "error"
            result["error"] = f"{type(exc).__name__}: {exc}"
            report["ok"] = False
        report["modules"][module_name] = result

    java_cmd = shutil.which("java")
    if not java_cmd:
        report["java"] = {"available": False, "error": "java command not found on PATH"}
        report["ok"] = False
    else:
        try:
            proc = subprocess.run(
                ["java", "-version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
            version_text = (proc.stderr or proc.stdout).splitlines()[0] if (proc.stderr or proc.stdout) else ""
            report["java"] = {"available": proc.returncode == 0, "version_line": version_text}
            if proc.returncode != 0:
                report["ok"] = False
        except Exception as exc:  # pylint: disable=broad-except
            report["java"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}
            report["ok"] = False
    return report


def plan_from_args(args: argparse.Namespace) -> Dict[str, Any]:
    master = args.master or f"local[{args.processes_count}]"
    download_kwargs: Dict[str, Any] = {
        "url_list": args.url_list or "<required-with---run>",
        "image_size": args.image_size,
        "output_folder": args.output_folder or "<required-with---run>",
        "processes_count": args.processes_count,
        "thread_count": args.thread_count,
        "output_format": args.output_format,
        "input_format": args.input_format,
        "url_col": args.url_col,
        "caption_col": args.caption_col,
        "enable_wandb": args.enable_wandb,
        "wandb_project": args.wandb_project,
        "number_sample_per_shard": args.number_sample_per_shard,
        "distributor": "pyspark",
        "subjob_size": args.subjob_size,
        "max_shard_retry": args.max_shard_retry,
        "retries": args.retries,
    }
    return {
        "spark_session": {
            "master": master,
            "driver_memory": args.driver_memory,
            "app_name": "spark-stats",
            "ownership": "template-created session; stopped by this script after download",
        },
        "download_kwargs": download_kwargs,
        "notes": [
            "Dry-run mode does not import pyspark or img2dataset.",
            "For cluster mode, ensure workers can import img2dataset and access input/output paths.",
            "subjob_size counts reader shards per Spark batch; approximate samples per batch are subjob_size * number_sample_per_shard.",
        ],
    }


def print_plan(args: argparse.Namespace) -> None:
    print(json.dumps(plan_from_args(args), indent=2, sort_keys=True))
    print("\nTo execute, re-run with --run after reviewing paths, Spark master, and backend checks.")


def create_spark_session(args: argparse.Namespace):
    from pyspark.sql import SparkSession  # pylint: disable=import-outside-toplevel

    master = args.master or f"local[{args.processes_count}]"
    return (
        SparkSession.builder.config("spark.driver.memory", args.driver_memory)
        .master(master)
        .appName("spark-stats")
        .getOrCreate()
    )


def run_download(args: argparse.Namespace) -> None:
    if not args.url_list or not args.output_folder:
        raise SystemExit("--url-list and --output-folder are required when --run is used")

    backend_report = check_backends()
    if not backend_report["ok"]:
        print(json.dumps(backend_report, indent=2, sort_keys=True), file=sys.stderr)
        raise SystemExit("Backend check failed; install PySpark/img2dataset and Java before running.")

    print(json.dumps(plan_from_args(args), indent=2, sort_keys=True))

    from img2dataset import download  # pylint: disable=import-outside-toplevel

    spark = create_spark_session(args)
    try:
        kwargs = plan_from_args(args)["download_kwargs"]
        download(**kwargs)
    finally:
        spark.stop()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.check_backends:
        print(json.dumps(check_backends(), indent=2, sort_keys=True))

    if args.dry_run:
        print_plan(args)
    else:
        run_download(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
