#!/usr/bin/env python3
"""Quick package-install smoke check for automl-gs.

This helper stays within the current Python environment and does not depend on
network access or the original repository checkout being opened in an editor.
"""

from __future__ import annotations

import argparse
import inspect
import subprocess
import sys
from importlib import metadata
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify automl_gs import, CLI help, and an optional backend import.",
    )
    parser.add_argument(
        "--backend",
        choices=("none", "xgboost", "tensorflow"),
        default="none",
        help="Optional backend import to verify alongside the package. Default: none.",
    )
    return parser


def run_cli_help() -> None:
    candidate = Path(sys.prefix) / ("Scripts" if sys.platform.startswith("win") else "bin") / "automl_gs"
    cmd = [str(candidate), "-h"] if candidate.exists() else [sys.executable, "-m", "automl_gs.automl_gs", "-h"]
    subprocess.run(cmd, check=True)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        from automl_gs import automl_grid_search
    except Exception as exc:
        print(f"automl_gs import failed: {exc}", file=sys.stderr)
        return 1

    try:
        version = metadata.version("automl_gs")
    except metadata.PackageNotFoundError as exc:
        print(f"distribution metadata missing: {exc}", file=sys.stderr)
        return 1

    print(f"automl_gs version: {version}")
    print(f"automl_grid_search signature: {inspect.signature(automl_grid_search)}")

    try:
        run_cli_help()
    except subprocess.CalledProcessError as exc:
        print(f"CLI help check failed with exit code {exc.returncode}", file=sys.stderr)
        return 1

    if args.backend == "xgboost":
        try:
            import xgboost  # type: ignore
        except Exception as exc:
            print(f"xgboost import failed: {exc}", file=sys.stderr)
            return 1
        print(f"xgboost version: {xgboost.__version__}")
    elif args.backend == "tensorflow":
        try:
            import tensorflow  # type: ignore
        except Exception as exc:
            print(f"tensorflow import failed: {exc}", file=sys.stderr)
            return 1
        print(f"tensorflow version: {tensorflow.__version__}")

    print("automl-gs install smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
