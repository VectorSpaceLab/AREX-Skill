#!/usr/bin/env python3
"""Safely copy images into Animal/No_animal folders from detection JSON.

This helper intentionally uses only the standard library. It never moves or
removes source files, rejects paths that escape the supplied source root, and
supports a deterministic --self-test without model weights or image downloads.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _relative_image_id(value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("each annotation img_id must be a non-empty string")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"img_id must be a relative, non-traversing path: {value!r}")
    # Normalize platform separators while retaining nested directories.
    candidate = Path(*[part for part in candidate.parts if part not in ("", ".")])
    if not candidate.parts:
        raise ValueError("img_id resolves to an empty path")
    return candidate


def _load_annotations(json_path: Path, threshold: float) -> dict[Path, bool]:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read detection JSON {json_path}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("annotations"), list):
        raise ValueError("detection JSON must contain an annotations list")

    decisions: dict[Path, bool] = {}
    for index, item in enumerate(payload["annotations"]):
        if not isinstance(item, dict):
            raise ValueError(f"annotation {index} must be an object")
        relative = _relative_image_id(item.get("img_id"))
        categories = item.get("category")
        confidences = item.get("confidence")
        if not isinstance(categories, list) or not isinstance(confidences, list):
            raise ValueError(f"annotation {index} needs category and confidence lists")
        if len(categories) != len(confidences):
            raise ValueError(f"annotation {index} category/confidence lengths differ")
        is_animal = decisions.get(relative, False)
        for category, confidence in zip(categories, confidences):
            if not isinstance(category, int) or isinstance(category, bool):
                raise ValueError(f"annotation {index} category ids must be integers")
            if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
                raise ValueError(f"annotation {index} has a non-numeric confidence")
            if not math.isfinite(float(confidence)):
                raise ValueError(f"annotation {index} has a non-finite confidence")
            # Match PytorchWildlife's category-0 and strict `>` behavior.
            is_animal = is_animal or (category == 0 and float(confidence) > threshold)
        decisions[relative] = is_animal
    return decisions


def separate(json_path: Path, source_root: Path, destination_root: Path,
             threshold: float, overwrite: bool = False) -> dict[str, int]:
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    source_root = source_root.expanduser().resolve()
    destination_root = destination_root.expanduser().resolve()
    json_path = json_path.expanduser().resolve()
    if not source_root.is_dir():
        raise ValueError(f"source root is not a directory: {source_root}")
    if not json_path.is_file():
        raise ValueError(f"detection JSON is not a file: {json_path}")
    if destination_root == source_root or _inside(destination_root, source_root):
        raise ValueError("destination must be outside source root to avoid re-ingestion")

    decisions = _load_annotations(json_path, threshold)
    counts = {"Animal": 0, "No_animal": 0}
    for relative, is_animal in decisions.items():
        source = (source_root / relative).resolve()
        if not _inside(source, source_root) or not source.is_file():
            raise ValueError(f"source image is missing or escapes source root: {relative}")
        folder = "Animal" if is_animal else "No_animal"
        target = destination_root / folder / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not overwrite:
            raise FileExistsError(f"refusing to overwrite existing output: {target}")
        shutil.copy2(source, target)
        counts[folder] += 1
    return counts


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Copy detection-positive and negative images safely.")
    parser.add_argument("--json", dest="json_path", type=Path, help="detection JSON with an annotations list")
    parser.add_argument("--source-root", type=Path, help="root containing the relative img_id paths")
    parser.add_argument("--destination", type=Path, help="new output root for Animal and No_animal")
    parser.add_argument("--threshold", type=float, default=0.2, help="strict category-0 confidence cutoff (default: 0.2)")
    parser.add_argument("--overwrite", action="store_true", help="allow replacing existing copied files")
    parser.add_argument("--self-test", action="store_true", help="run a tiny fixture check and exit")
    return parser


def _self_test() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "source"
        destination = root / "out"
        (source / "nested").mkdir(parents=True)
        (source / "nested" / "animal.jpg").write_bytes(b"animal")
        (source / "empty.jpg").write_bytes(b"empty")
        data = {"annotations": [
            {"img_id": "nested/animal.jpg", "category": [0], "confidence": [0.21]},
            {"img_id": "empty.jpg", "category": [], "confidence": []},
        ]}
        report = root / "detections.json"
        report.write_text(json.dumps(data), encoding="utf-8")
        assert separate(report, source, destination, 0.2) == {"Animal": 1, "No_animal": 1}
        assert (destination / "Animal" / "nested" / "animal.jpg").read_bytes() == b"animal"
        assert (destination / "No_animal" / "empty.jpg").read_bytes() == b"empty"
        assert (source / "nested" / "animal.jpg").exists()
    print("self-test passed")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.self_test:
        _self_test()
        return 0
    if not args.json_path or not args.source_root or not args.destination:
        _parser().error("--json, --source-root, and --destination are required unless --self-test is used")
    try:
        print(json.dumps(separate(args.json_path, args.source_root, args.destination,
                                  args.threshold, args.overwrite), sort_keys=True))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
