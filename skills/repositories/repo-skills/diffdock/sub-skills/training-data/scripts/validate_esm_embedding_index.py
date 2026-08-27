#!/usr/bin/env python3
"""Validate DiffDock ESM embedding indexes without importing torch by default."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional


EMBEDDING_EXTENSIONS = {".pt", ".pth"}


def read_expected_ids(paths: list[str], max_ids: Optional[int]) -> tuple[list[str], list[str]]:
    ids: list[str] = []
    warnings: list[str] = []
    for path_text in paths:
        path = Path(path_text)
        if not path.exists():
            warnings.append(f"expected-id source does not exist: {path}")
            continue
        try:
            with path.open("r", encoding="utf-8") as handle:
                first = handle.readline()
                handle.seek(0)
                if first.startswith(">"):
                    for line in handle:
                        line = line.strip()
                        if line.startswith(">"):
                            ids.append(line[1:].split()[0])
                            if max_ids is not None and len(ids) >= max_ids:
                                break
                else:
                    for line in handle:
                        value = line.strip().split(",")[0]
                        if not value or value.startswith("#"):
                            continue
                        if value in {"complex_name", "protein_path", "ligand", "ligand_description"}:
                            continue
                        ids.append(value)
                        if max_ids is not None and len(ids) >= max_ids:
                            break
        except UnicodeDecodeError:
            warnings.append(f"expected-id source is not UTF-8 text: {path}")
    return ids, warnings


def summarize_directory(path: Path, expected_ids: list[str]) -> dict[str, Any]:
    files = [entry for entry in path.iterdir() if entry.is_file()]
    pt_files = sorted([entry for entry in files if entry.suffix.lower() in EMBEDDING_EXTENSIONS])
    keys = {entry.stem for entry in pt_files}
    expected_prefix_hits = {}
    missing_prefixes = []
    for expected_id in expected_ids:
        matches = sorted(key for key in keys if key == expected_id or key.startswith(expected_id + "_chain_"))
        expected_prefix_hits[expected_id] = matches[:5]
        if not matches:
            missing_prefixes.append(expected_id)
    return {
        "kind": "directory",
        "path": str(path),
        "exists": path.exists(),
        "file_count": len(files),
        "pt_file_count": len(pt_files),
        "sample_pt_files": [entry.name for entry in pt_files[:10]],
        "expected_ids_checked": len(expected_ids),
        "missing_expected_ids": missing_prefixes[:50],
        "missing_expected_ids_count": len(missing_prefixes),
        "sample_matches": dict(list(expected_prefix_hits.items())[:10]),
    }


def summarize_pt_metadata(path: Path, expected_ids: list[str]) -> dict[str, Any]:
    return {
        "kind": "pt_file_metadata_only",
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "expected_ids_checked": len(expected_ids),
        "missing_expected_ids": None,
        "note": "Pass --load-pt to import torch and inspect aggregate keys; default mode avoids heavy imports.",
    }


def summarize_pt_with_torch(path: Path, expected_ids: list[str]) -> dict[str, Any]:
    try:
        import torch  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional environment
        return {
            "kind": "pt_file_torch_load_failed",
            "path": str(path),
            "exists": path.exists(),
            "error": f"torch import failed: {exc}",
            "advice": "Install/use the DiffDock training environment or validate the per-sequence embedding directory instead.",
        }

    try:
        obj = torch.load(path, map_location="cpu")
    except Exception as exc:  # pragma: no cover - depends on optional data
        return {
            "kind": "pt_file_torch_load_failed",
            "path": str(path),
            "exists": path.exists(),
            "error": f"torch.load failed: {exc}",
        }

    if isinstance(obj, dict):
        keys = {str(key) for key in obj.keys()}
        missing = []
        sample_shapes = {}
        for key in list(keys)[:10]:
            value = obj[key] if key in obj else obj.get(key)
            shape = getattr(value, "shape", None)
            sample_shapes[key] = list(shape) if shape is not None else type(value).__name__
        for expected_id in expected_ids:
            if not any(key == expected_id or key.startswith(expected_id + "_chain_") for key in keys):
                missing.append(expected_id)
        return {
            "kind": "pt_file_loaded",
            "path": str(path),
            "exists": True,
            "object_type": "dict",
            "key_count": len(keys),
            "sample_keys": sorted(keys)[:20],
            "sample_shapes": sample_shapes,
            "expected_ids_checked": len(expected_ids),
            "missing_expected_ids": missing[:50],
            "missing_expected_ids_count": len(missing),
        }

    return {
        "kind": "pt_file_loaded",
        "path": str(path),
        "exists": True,
        "object_type": type(obj).__name__,
        "warning": "Expected a dict-like aggregate mapping; DiffDock ESM conversion scripts save dictionaries.",
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Embedding directory or aggregate .pt path.")
    parser.add_argument("--expect-ids", action="append", default=[], help="Split, FASTA, or text file containing expected complex/sequence ids. Repeat as needed.")
    parser.add_argument("--max-ids", type=int, default=200, help="Maximum expected ids to read across files.")
    parser.add_argument("--load-pt", action="store_true", help="Import torch and inspect .pt aggregate keys. Not used by default.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    path = Path(args.path)
    expected_ids, warnings = read_expected_ids(args.expect_ids, args.max_ids)

    if not path.exists():
        report = {"kind": "missing", "path": str(path), "exists": False}
    elif path.is_dir():
        report = summarize_directory(path, expected_ids)
    elif path.is_file() and path.suffix.lower() in EMBEDDING_EXTENSIONS:
        report = summarize_pt_with_torch(path, expected_ids) if args.load_pt else summarize_pt_metadata(path, expected_ids)
    else:
        report = {
            "kind": "unsupported_path",
            "path": str(path),
            "exists": True,
            "warning": "Expected an embeddings directory or .pt/.pth aggregate file.",
        }

    missing_count = report.get("missing_expected_ids_count")
    report["warnings"] = warnings + ([report["warning"]] if "warning" in report else [])
    report["safe"] = True
    report["torch_imported"] = bool(args.load_pt and path.is_file() and path.suffix.lower() in EMBEDDING_EXTENSIONS)
    report["ok"] = bool(report.get("exists")) and missing_count in (None, 0)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
