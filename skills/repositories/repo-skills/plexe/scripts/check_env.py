#!/usr/bin/env python3
"""Smoke-check the Plexe installation and optional runtime features."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from importlib import metadata

OPTIONAL_PACKAGES = ["pyspark", "tensorflow", "keras", "torch", "catboost", "lightgbm", "streamlit", "plotly"]


def _version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "missing"


def _print_versions() -> None:
    print(f"Python: {sys.version.split()[0]}")
    print(f"plexe: {_version('plexe')}")
    print(f"OPENAI_API_KEY: {'set' if os.getenv('OPENAI_API_KEY') else 'missing'}")
    print(f"ANTHROPIC_API_KEY: {'set' if os.getenv('ANTHROPIC_API_KEY') else 'missing'}")
    for name in OPTIONAL_PACKAGES:
        print(f"{name}: {_version(name)}")


def _run_help(module: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", module, "--help"],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"{module} --help failed")
    first_line = result.stdout.splitlines()[0] if result.stdout.splitlines() else f"{module} --help"
    print(f"{module}: {first_line}")


def _spark_smoke() -> None:
    from plexe.config import Config
    from plexe.execution.dataproc.session import get_or_create_spark_session, stop_spark_session

    spark = get_or_create_spark_session(Config(spark_mode="local", spark_local_cores=1, spark_driver_memory="1g"))
    try:
        print(f"spark: {spark.version} / {spark.sparkContext.appName}")
    finally:
        stop_spark_session()


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check a Plexe installation")
    parser.add_argument("--cli", action="store_true", help="Run `python -m plexe.main --help`")
    parser.add_argument("--dashboard", action="store_true", help="Run `python -m plexe.viz --help`")
    parser.add_argument("--spark", action="store_true", help="Start a tiny local Spark session")
    parser.add_argument("--all", action="store_true", help="Run every available check")
    args = parser.parse_args()

    if args.all:
        args.cli = True
        args.dashboard = True
        args.spark = True

    _print_versions()

    if args.cli:
        _run_help("plexe.main")
    if args.dashboard:
        _run_help("plexe.viz")
    if args.spark:
        _spark_smoke()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
