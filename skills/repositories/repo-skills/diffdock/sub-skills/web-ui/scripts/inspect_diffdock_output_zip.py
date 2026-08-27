#!/usr/bin/env python3
"""Inspect a DiffDock Gradio UI output zip and print a JSON summary.

This helper intentionally avoids importing Gradio, DiffDock, RDKit, Torch, or
other heavy runtime dependencies. It adapts the lightweight output parsing
conventions used by DiffDock's web UI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

_RANK_RE = re.compile(r"^rank(?P<rank>\d+)(?:_confidence(?P<confidence>[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?))?$")
_TEXT_SUFFIXES = {".pdb", ".sdf", ".log", ".txt", ".yaml", ".yml", ".csv", ".json"}


def parse_ligand_filename(filename: str) -> Dict[str, Any]:
    """Parse DiffDock UI ranked SDF names into rank/confidence metadata."""
    path_name = filename.replace("\\", "/")
    basename = os.path.basename(path_name)
    stem, suffix = os.path.splitext(basename)
    if suffix.lower() != ".sdf":
        return {
            "basename": basename,
            "rank": None,
            "confidence": None,
            "parse_status": "not_sdf",
        }

    match = _RANK_RE.match(stem)
    if not match:
        return {
            "basename": basename,
            "rank": None,
            "confidence": None,
            "parse_status": "unrecognized_sdf_name",
        }

    confidence_text = match.group("confidence")
    return {
        "basename": basename,
        "rank": int(match.group("rank")),
        "confidence": float(confidence_text) if confidence_text is not None else None,
        "parse_status": "ok_without_confidence" if confidence_text is None else "ok",
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _decode_text(data: bytes) -> Tuple[bool, Optional[str]]:
    if not data:
        return False, "empty"
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False, "not_utf8"
    return True, None


def _entry_summary(path: str, data: bytes, include_hash: bool) -> Dict[str, Any]:
    suffix = Path(path).suffix.lower()
    text_decodable, text_warning = _decode_text(data) if suffix in _TEXT_SUFFIXES else (False, None)
    summary: Dict[str, Any] = {
        "path": path,
        "size_bytes": len(data),
        "has_content": bool(data),
        "text_decodable": text_decodable,
    }
    if text_warning:
        summary["content_warning"] = text_warning
    if include_hash:
        summary["sha256"] = _sha256(data)
    return summary


def _sort_sdf_entries(entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        entries,
        key=lambda item: (
            item.get("rank") is None,
            item.get("rank") if item.get("rank") is not None else 1_000_000,
            item.get("path", ""),
        ),
    )


def inspect_zip(zip_path: Path, include_hash: bool = True) -> Dict[str, Any]:
    if not zip_path.exists():
        raise FileNotFoundError(f"zip file not found: {zip_path}")
    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"not a valid zip file: {zip_path}")

    pdb_files: List[Dict[str, Any]] = []
    sdf_files: List[Dict[str, Any]] = []
    other_files: List[Dict[str, Any]] = []
    warnings: List[str] = []

    with zipfile.ZipFile(zip_path, "r") as archive:
        file_names = [name for name in archive.namelist() if not name.endswith("/")]
        for name in file_names:
            data = archive.read(name)
            suffix = Path(name).suffix.lower()
            entry = _entry_summary(name, data, include_hash=include_hash)

            if suffix == ".pdb":
                pdb_files.append(entry)
            elif suffix == ".sdf":
                parsed = parse_ligand_filename(name)
                entry.update(parsed)
                sdf_files.append(entry)
            else:
                other_files.append(entry)

    sdf_files = _sort_sdf_entries(sdf_files)

    malformed_sdfs = [entry["path"] for entry in sdf_files if entry.get("parse_status") == "unrecognized_sdf_name"]
    no_confidence_sdfs = [
        entry["path"]
        for entry in sdf_files
        if entry.get("parse_status") == "ok_without_confidence"
    ]
    confidence_sdfs = [entry for entry in sdf_files if entry.get("confidence") is not None]

    if not pdb_files:
        warnings.append("no_pdb_files_found")
    if not sdf_files:
        warnings.append("no_sdf_files_found")
    if malformed_sdfs:
        warnings.append("some_sdf_filenames_do_not_match_rank_pattern")
    if no_confidence_sdfs:
        warnings.append("some_ranked_sdf_files_have_no_confidence_label")
    if sdf_files and not confidence_sdfs:
        warnings.append("ui_dropdown_would_have_no_confidence_labelled_sdf_entries")

    return {
        "zip_path": str(zip_path),
        "member_count": len(pdb_files) + len(sdf_files) + len(other_files),
        "pdb_files": pdb_files,
        "sdf_files": sdf_files,
        "other_files": other_files,
        "visualization_summary": {
            "has_pdb_for_viewer": bool(pdb_files),
            "confidence_labelled_sdf_count": len(confidence_sdfs),
            "would_create_dropdown_entries": bool(confidence_sdfs),
            "would_render_3d_viewer": bool(pdb_files and confidence_sdfs),
            "first_pdb_path": pdb_files[0]["path"] if pdb_files else None,
        },
        "warnings": warnings,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a DiffDock Gradio UI output zip and print a JSON summary.",
    )
    parser.add_argument("zip_path", help="Path to a DiffDock UI output .zip file.")
    parser.add_argument(
        "--no-hash",
        action="store_true",
        help="Omit SHA-256 hashes from file entries.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level. Use 0 for compact single-line JSON.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        summary = inspect_zip(Path(args.zip_path), include_hash=not args.no_hash)
    except (FileNotFoundError, ValueError, zipfile.BadZipFile) as exc:
        parser.exit(2, f"error: {exc}\n")

    indent = None if args.indent == 0 else args.indent
    print(json.dumps(summary, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
