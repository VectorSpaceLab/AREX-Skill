#!/usr/bin/env python3
"""Verify the Petastorm import surface and report missing optional extras.

Run:
    python scripts/check_install.py

The script is read-only and safe to run from any working directory.
"""
from __future__ import annotations

import importlib
import shutil
import sys


CORE_IMPORTS = [
    "petastorm",
    "petastorm.reader",
    "petastorm.spark",
    "petastorm.tf_utils",
    "petastorm.pytorch",
    "petastorm.etl.dataset_metadata",
    "petastorm.tools.copy_dataset",
    "petastorm.benchmark.cli",
    "petastorm.tools.spark_session_cli",
]

OPTIONAL_IMPORTS = [
    "tensorflow.compat.v1",
    "torch",
    "cv2",
    "s3fs",
    "gcsfs",
]


def _try_import(name: str):
    try:
        module = importlib.import_module(name)
        print(f"core_import_ok: {name}")
        return module, None
    except Exception as exc:  # pragma: no cover - handled in CLI output
        print(f"core_import_failed: {name}: {type(exc).__name__}: {exc}")
        return None, exc


def main() -> int:
    failures = 0

    try:
        import pyarrow  # noqa: F401
        print("core_import_ok: pyarrow")
    except Exception as exc:
        print(f"core_import_failed: pyarrow: {type(exc).__name__}: {exc}")
        return 1

    try:
        import petastorm
        from petastorm import make_reader, make_batch_reader
        print(f"petastorm_version: {petastorm.__version__}")
        print(f"public_api_ok: {make_reader.__name__}, {make_batch_reader.__name__}")
    except Exception as exc:
        print(f"core_import_failed: petastorm: {type(exc).__name__}: {exc}")
        return 1

    for name in CORE_IMPORTS:
        module, exc = _try_import(name)
        if exc is not None:
            failures += 1

    # Keep the import order recommended by the repository docs.
    for name in OPTIONAL_IMPORTS:
        try:
            importlib.import_module(name)
            print(f"optional_import_ok: {name}")
        except Exception as exc:
            print(f"optional_import_missing: {name}: {type(exc).__name__}: {exc}")

    cli_names = [
        "petastorm-copy-dataset.py",
        "petastorm-generate-metadata.py",
        "petastorm-throughput.py",
    ]
    missing = []
    for cli_name in cli_names:
        cli_path = shutil.which(cli_name)
        if cli_path:
            print(f"cli_on_path: {cli_name}: {cli_path}")
        else:
            print(f"cli_missing: {cli_name}")
            missing.append(cli_name)

    return 1 if failures or missing else 0


if __name__ == "__main__":
    sys.exit(main())
