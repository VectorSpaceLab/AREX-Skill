#!/usr/bin/env python3
"""Inspect Yellowbrick dataset cache state without downloads or deletes.

The script reads the installed Yellowbrick dataset manifest when available,
resolves the selected cache directory, and reports local files/signatures as
JSON. It never imports loader objects in a way that constructs Dataset/Corpus
instances, never calls the downloader, and never removes files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

CORPUS_DATASETS = {"hobbies"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a local Yellowbrick dataset cache without downloading, "
            "deleting, or creating dataset files."
        )
    )
    parser.add_argument(
        "--data-home",
        dest="data_home",
        help=(
            "cache directory to inspect; defaults to $YELLOWBRICK_DATA or the "
            "installed package fixture directory"
        ),
    )
    parser.add_argument(
        "--dataset",
        action="append",
        default=[],
        help=(
            "limit inspection to a dataset name; repeat the flag or pass a "
            "comma-separated list"
        ),
    )
    return parser.parse_args()


def emit(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def load_yellowbrick_metadata() -> tuple[dict[str, dict[str, str]], str, Callable[[str], str]]:
    """Load manifest metadata from the installed Yellowbrick package."""
    from yellowbrick.datasets.loaders import DATASETS
    from yellowbrick.datasets.path import FIXTURES
    from yellowbrick.datasets.signature import sha256sum

    return DATASETS, FIXTURES, sha256sum


def expand_dataset_args(values: list[str]) -> list[str]:
    names: list[str] = []
    for value in values:
        for part in value.split(","):
            name = part.strip()
            if name:
                names.append(name)
    return names


def resolve_data_home(value: str | None, default_fixture: str) -> tuple[Path, str]:
    if value is not None:
        raw = value
        source = "argument"
    elif os.environ.get("YELLOWBRICK_DATA"):
        raw = os.environ["YELLOWBRICK_DATA"]
        source = "YELLOWBRICK_DATA"
    else:
        raw = default_fixture
        source = "yellowbrick_default_fixture"

    expanded = os.path.expanduser(os.path.expandvars(str(raw)))
    return Path(expanded), source


def path_state(path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
        "size_bytes": None,
    }
    if path.is_file():
        try:
            record["size_bytes"] = path.stat().st_size
        except OSError as exc:
            record["stat_error"] = f"{exc.__class__.__name__}: {exc}"
    return record


def archive_state(
    name: str,
    data_home: Path,
    expected_signature: str,
    sha256sum: Callable[[str], str],
) -> dict[str, Any]:
    archive = data_home / f"{name}.zip"
    record = path_state(archive)
    record.update(
        {
            "expected_sha256": expected_signature,
            "actual_sha256": None,
            "signature_ok": None,
            "status": "missing",
        }
    )

    if not archive.exists():
        return record
    if not archive.is_file():
        record["status"] = "not-a-file"
        return record

    try:
        actual = sha256sum(str(archive))
    except OSError as exc:
        record["status"] = f"error:{exc.__class__.__name__}"
        record["signature_error"] = str(exc)
        return record

    record["actual_sha256"] = actual
    record["signature_ok"] = actual == expected_signature
    record["status"] = "signature-ok" if record["signature_ok"] else "signature-mismatch"
    return record


def inspect_dataset(
    name: str,
    meta: dict[str, str],
    data_home: Path,
    sha256sum: Callable[[str], str],
) -> dict[str, Any]:
    root = data_home / name
    is_corpus = name in CORPUS_DATASETS
    files: dict[str, Any] = {
        "README.md": path_state(root / "README.md"),
    }

    if is_corpus:
        labels: list[str] = []
        document_count: int | None = None
        if root.is_dir():
            try:
                labels = sorted(child.name for child in root.iterdir() if child.is_dir())
                document_count = sum(1 for child in root.rglob("*.txt") if child.is_file())
            except OSError:
                labels = []
                document_count = None
        ready_for_loader = root.is_dir() and bool(labels) and bool(document_count)
        return {
            "name": name,
            "kind": "corpus",
            "loader": f"load_{name}",
            "return_dataset_supported": False,
            "cache_dir": path_state(root),
            "archive": archive_state(name, data_home, meta["signature"], sha256sum),
            "files": files,
            "labels": labels,
            "label_count": len(labels),
            "document_count": document_count,
            "loader_would_attempt_download": not root.is_dir(),
            "ready_for_loader": ready_for_loader,
        }

    files.update(
        {
            f"{name}.csv.gz": path_state(root / f"{name}.csv.gz"),
            f"{name}.npz": path_state(root / f"{name}.npz"),
            "meta.json": path_state(root / "meta.json"),
            "citation.bib": path_state(root / "citation.bib"),
        }
    )
    ready_for_loader = (
        root.is_dir()
        and files[f"{name}.csv.gz"]["is_file"]
        and files[f"{name}.npz"]["is_file"]
        and files["meta.json"]["is_file"]
    )
    return {
        "name": name,
        "kind": "tabular",
        "loader": f"load_{name}",
        "return_dataset_supported": True,
        "cache_dir": path_state(root),
        "archive": archive_state(name, data_home, meta["signature"], sha256sum),
        "files": files,
        "loader_would_attempt_download": not root.is_dir(),
        "ready_for_loader": ready_for_loader,
    }


def main() -> int:
    args = parse_args()

    try:
        datasets, default_fixture, sha256sum = load_yellowbrick_metadata()
    except Exception as exc:  # pragma: no cover - depends on caller environment
        emit(
            {
                "status": "yellowbrick-unavailable",
                "exit_code": 1,
                "network_used": False,
                "deleted_files": False,
                "error": {
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                },
            }
        )
        return 1

    data_home, data_home_source = resolve_data_home(args.data_home, default_fixture)
    valid_names = sorted(datasets)
    requested = expand_dataset_args(args.dataset)
    selected = requested if requested else valid_names
    invalid = [name for name in selected if name not in datasets]

    if invalid:
        emit(
            {
                "status": "invalid-dataset",
                "exit_code": 2,
                "network_used": False,
                "deleted_files": False,
                "data_home": str(data_home),
                "data_home_source": data_home_source,
                "requested": selected,
                "invalid_datasets": invalid,
                "valid_dataset_names": valid_names,
            }
        )
        return 2

    inspected = [
        inspect_dataset(name, datasets[name], data_home, sha256sum) for name in selected
    ]
    missing = [item["name"] for item in inspected if not item["cache_dir"]["is_dir"]]
    incomplete = [item["name"] for item in inspected if not item["ready_for_loader"]]
    signature_mismatch = [
        item["name"]
        for item in inspected
        if item["archive"].get("status") == "signature-mismatch"
    ]

    emit(
        {
            "status": "ok",
            "exit_code": 0,
            "network_used": False,
            "deleted_files": False,
            "manifest_source": "installed yellowbrick.datasets.loaders.DATASETS",
            "data_home": str(data_home),
            "data_home_source": data_home_source,
            "data_home_exists": data_home.exists(),
            "requested": selected,
            "dataset_count": len(inspected),
            "summary": {
                "missing_dataset_dirs": missing,
                "incomplete_for_loader": incomplete,
                "signature_mismatch": signature_mismatch,
            },
            "datasets": inspected,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
