#!/usr/bin/env python3
"""Validate a ProteinMPNN training data directory without scanning all tensors."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from pathlib import Path
from typing import Iterable

REQUIRED_ROOT_FILES = ("list.csv", "valid_clusters.txt", "test_clusters.txt")
CHAIN_REQUIRED_KEYS = ("seq", "xyz", "mask", "bfac", "occ")
META_SUGGESTED_KEYS = (
    "method",
    "date",
    "resolution",
    "chains",
    "tm",
    "asmb_ids",
    "asmb_details",
    "asmb_method",
    "asmb_chains",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check ProteinMPNN training data files, cluster lists, and sampled .pt paths."
    )
    parser.add_argument("--data-root", required=True, help="Training data root containing list.csv and pdb/.")
    parser.add_argument("--sample-rows", type=int, default=20, help="Number of list.csv rows to sample for .pt path checks.")
    parser.add_argument("--no-torch-load", action="store_true", help="Only check paths; do not import torch or inspect .pt keys.")
    return parser.parse_args()


def report(status: str, message: str) -> None:
    print(f"[{status}] {message}")


def read_cluster_ids(path: Path) -> set[int]:
    cluster_ids: set[int] = set()
    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            cluster_ids.add(int(line))
        except ValueError:
            raise ValueError(f"{path.name}:{line_number} is not an integer cluster id: {line!r}") from None
    return cluster_ids


def iter_list_rows(path: Path) -> Iterable[tuple[int, dict[str, str]]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"CHAINID", "DEPOSITION", "RESOLUTION", "HASH", "CLUSTER", "SEQUENCE"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"list.csv missing columns: {', '.join(sorted(missing))}")
        for row_number, row in enumerate(reader, start=2):
            yield row_number, row


def tensor_paths(data_root: Path, chain_id: str) -> tuple[Path, Path]:
    if "_" not in chain_id:
        raise ValueError(f"CHAINID must look like PDBID_CHAINID, got {chain_id!r}")
    pdb_id, chain = chain_id.split("_", 1)
    if len(pdb_id) < 3 or not chain:
        raise ValueError(f"CHAINID must include a PDB id and chain id, got {chain_id!r}")
    prefix = data_root / "pdb" / pdb_id[1:3] / pdb_id
    return prefix.with_suffix(".pt"), Path(f"{prefix}_{chain}.pt")


def maybe_load_torch(no_torch_load: bool):
    if no_torch_load:
        return None
    if importlib.util.find_spec("torch") is None:
        report("WARN", "PyTorch is not importable; skipping shallow .pt key checks")
        return None
    import torch

    return torch


def check_keys(torch_module, path: Path, required_keys: tuple[str, ...], label: str) -> bool:
    try:
        try:
            obj = torch_module.load(path, map_location="cpu", weights_only=False)
        except TypeError:
            obj = torch_module.load(path, map_location="cpu")
    except Exception as exc:  # noqa: BLE001 - show concise data issue to CLI users.
        report("FAIL", f"could not load {label} tensor {path}: {exc}")
        return False
    if not isinstance(obj, dict):
        report("FAIL", f"{label} tensor {path} is {type(obj).__name__}, expected dict-like checkpoint")
        return False
    missing = [key for key in required_keys if key not in obj]
    if missing:
        report("FAIL", f"{label} tensor {path} missing keys: {', '.join(missing)}")
        return False
    return True


def main() -> int:
    args = parse_args()
    data_root = Path(args.data_root).expanduser()
    failures = 0

    if not data_root.is_dir():
        report("FAIL", f"data root does not exist or is not a directory: {data_root}")
        return 2

    for filename in REQUIRED_ROOT_FILES:
        path = data_root / filename
        if path.is_file():
            report("OK", f"found {filename}")
        else:
            report("FAIL", f"missing {filename}")
            failures += 1

    pdb_dir = data_root / "pdb"
    if pdb_dir.is_dir():
        report("OK", "found pdb/ tensor directory")
    else:
        report("FAIL", "missing pdb/ tensor directory")
        failures += 1

    if failures:
        return 2

    try:
        valid_ids = read_cluster_ids(data_root / "valid_clusters.txt")
        test_ids = read_cluster_ids(data_root / "test_clusters.txt")
    except ValueError as exc:
        report("FAIL", str(exc))
        return 2
    report("OK", f"parsed {len(valid_ids)} validation clusters and {len(test_ids)} test clusters")

    sampled_rows: list[tuple[int, dict[str, str]]] = []
    total_rows = 0
    bad_rows = 0
    try:
        for row_number, row in iter_list_rows(data_root / "list.csv"):
            total_rows += 1
            try:
                float(row["RESOLUTION"])
                int(row["CLUSTER"])
            except ValueError:
                report("FAIL", f"list.csv:{row_number} has non-numeric RESOLUTION or CLUSTER")
                bad_rows += 1
            if len(sampled_rows) < max(args.sample_rows, 0):
                sampled_rows.append((row_number, row))
    except ValueError as exc:
        report("FAIL", str(exc))
        return 2

    if total_rows == 0:
        report("FAIL", "list.csv has no data rows")
        return 2
    if bad_rows:
        failures += bad_rows
    report("OK", f"read {total_rows} list.csv rows; checking {len(sampled_rows)} sampled rows")

    torch_module = maybe_load_torch(args.no_torch_load)
    seen_meta: set[Path] = set()
    for row_number, row in sampled_rows:
        chain_id = row["CHAINID"].strip()
        try:
            meta_path, chain_path = tensor_paths(data_root, chain_id)
        except ValueError as exc:
            report("FAIL", f"list.csv:{row_number}: {exc}")
            failures += 1
            continue

        if meta_path.is_file():
            report("OK", f"metadata exists for {chain_id}: {meta_path.relative_to(data_root)}")
            if torch_module is not None and meta_path not in seen_meta:
                if not check_keys(torch_module, meta_path, META_SUGGESTED_KEYS, "metadata"):
                    failures += 1
                seen_meta.add(meta_path)
        else:
            report("FAIL", f"missing metadata for {chain_id}: {meta_path.relative_to(data_root)}")
            failures += 1

        if chain_path.is_file():
            report("OK", f"chain tensor exists for {chain_id}: {chain_path.relative_to(data_root)}")
            if torch_module is not None:
                if not check_keys(torch_module, chain_path, CHAIN_REQUIRED_KEYS, "chain"):
                    failures += 1
        else:
            report("FAIL", f"missing chain tensor for {chain_id}: {chain_path.relative_to(data_root)}")
            failures += 1

    if failures:
        report("FAIL", f"layout check finished with {failures} issue(s)")
        return 1
    report("OK", "layout check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
