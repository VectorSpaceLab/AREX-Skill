#!/usr/bin/env python3
"""Offline validation for ChestAgentBench-style JSONL case manifests.

This helper never imports an API client and never fetches URL references. It
checks case shape and resolves local image references below an explicit root.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

IMAGE_FIELDS = ("images", "image_paths")
URL_FIELDS = ("image_source_urls", "image_urls")
REQUIRED_FIELDS = ("question_id", "question", "answer")


def _flatten(value: Any, field: str, path: str = "") -> Iterable[str]:
    """Yield strings from arbitrarily nested image arrays."""
    if isinstance(value, str):
        if value.strip():
            yield value.strip()
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            yield from _flatten(item, field, f"{path}[{index}]")
        return
    if value is None:
        return
    raise ValueError(f"{field}{path}: expected string, list, or null")


def _selected_field(record: dict[str, Any]) -> tuple[str | None, Any]:
    for field in IMAGE_FIELDS:
        if field in record:
            return field, record[field]
    return None, None


def _normalize_local_reference(reference: str) -> str:
    """Normalize quickstart-compatible relative figure references safely."""
    value = reference.strip().replace("\\", "/")
    parsed = urlparse(value)
    if parsed.scheme or value.startswith("//"):
        raise ValueError("URL reference is not a local image path")
    if os.path.isabs(value):
        raise ValueError("absolute image paths are not portable; use --root")
    while value.startswith("./"):
        value = value[2:]
    if value == "figures":
        raise ValueError("figures directory is not an image file")
    if value.startswith("figures/"):
        value = value[len("figures/") :]
    if not value or value == ".":
        raise ValueError("empty image path")
    parts = Path(value).parts
    if ".." in parts:
        raise ValueError("path traversal is not allowed")
    return Path(*parts).as_posix()


def _resolve(root: Path, reference: str) -> Path:
    normalized = _normalize_local_reference(reference)
    # Accept either a dataset root containing figures/ or the figures
    # directory itself. This mirrors the runner's leading-figures stripping
    # while keeping resolution local and deterministic.
    image_root = root / "figures" if (root / "figures").is_dir() else root
    candidate = (image_root / normalized).resolve()
    try:
        candidate.relative_to(image_root.resolve())
    except ValueError as exc:
        raise ValueError("image path escapes the declared root") from exc
    return candidate


def validate(manifest: Path, root: Path, max_cases: int | None = None) -> dict[str, Any]:
    """Validate up to max_cases records and return a JSON-safe summary."""
    if max_cases is not None and max_cases < 1:
        raise ValueError("--max-cases must be at least 1")
    if not manifest.is_file():
        raise FileNotFoundError(f"manifest not found: {manifest}")
    checked = 0
    valid = 0
    skip_candidates = 0
    errors: list[dict[str, Any]] = []
    with manifest.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            if max_cases is not None and checked >= max_cases:
                break
            checked += 1
            record: Any = None
            try:
                record = json.loads(raw)
                if not isinstance(record, dict):
                    raise ValueError("record must be a JSON object")
                missing = [key for key in REQUIRED_FIELDS if key not in record]
                if missing:
                    raise ValueError(f"missing required field(s): {', '.join(missing)}")
                for key in REQUIRED_FIELDS:
                    if not isinstance(record[key], str) or not record[key].strip():
                        raise ValueError(f"{key} must be a non-empty string")
                field, value = _selected_field(record)
                if field is None:
                    raise ValueError("missing local image field: images")
                refs = list(_flatten(value, field))
                if not refs:
                    skip_candidates += 1
                    valid += 1
                    continue
                for ref in refs:
                    image = _resolve(root, ref)
                    if not image.is_file():
                        raise FileNotFoundError(f"missing local image: {ref}")
                valid += 1
            except (json.JSONDecodeError, OSError, ValueError) as exc:
                errors.append(
                    {
                        "line": line_number,
                        "question_id": record.get("question_id") if isinstance(record, dict) else None,
                        "error": str(exc),
                    }
                )

    return {
        "manifest": manifest.name,
        "root": root.name or ".",
        "checked": checked,
        "valid": valid,
        "skip_candidates": skip_candidates,
        "errors": errors,
        "ok": not errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate local benchmark case JSONL and image references offline."
    )
    parser.add_argument("manifest", type=Path, help="JSONL case manifest")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="root for local image references (default: manifest parent)",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=None,
        help="validate only the first N non-empty records",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the summary as one JSON object instead of text",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = args.manifest.expanduser()
    root = (args.root or manifest.parent).expanduser()
    try:
        summary = validate(manifest, root, args.max_cases)
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(
            f"checked={summary['checked']} valid={summary['valid']} "
            f"skip_candidates={summary['skip_candidates']} errors={len(summary['errors'])}"
        )
        for item in summary["errors"]:
            identity = f" question_id={item['question_id']}" if item["question_id"] else ""
            print(f"line={item['line']}{identity}: {item['error']}", file=sys.stderr)
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
