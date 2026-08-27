#!/usr/bin/env python3
"""Validate img2img-turbo paired or unpaired training dataset layouts.

This checker is deterministic and intentionally lightweight: it only inspects
filesystem paths, filenames, fixed prompt text files, and paired prompt JSON. It
does not import tokenizers, model packages, CUDA, or metric code.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

COMMON_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
UNPAIRED_TRAIN_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".gif")
UNPAIRED_VAL_EXTS = (".jpg", ".jpeg", ".png", ".bmp")


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def top_level_images(folder: Path, exts: Iterable[str]) -> list[Path]:
    if not folder.is_dir():
        return []
    allowed = set(exts)
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix in allowed)


def recursive_common_images(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in COMMON_IMAGE_EXTS)


def files_with_case_mismatched_ext(folder: Path, allowed_lower: Iterable[str]) -> list[Path]:
    if not folder.is_dir():
        return []
    allowed = set(allowed_lower)
    out: list[Path] = []
    for p in sorted(folder.iterdir()):
        if not p.is_file():
            continue
        lower = p.suffix.lower()
        if lower in allowed and p.suffix not in allowed:
            out.append(p)
    return out


def load_json_object(path: Path, reporter: Reporter, label: str) -> dict[str, object] | None:
    if not path.is_file():
        reporter.error(f"missing {label}: {path}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        reporter.error(f"invalid JSON in {label} ({path}): {exc}")
        return None
    if not isinstance(data, dict):
        reporter.error(f"{label} must be a JSON object mapping image filename to prompt: {path}")
        return None
    return data


def unsafe_key(key: str) -> bool:
    candidate = Path(key)
    return candidate.is_absolute() or ".." in candidate.parts or key in {"", "."}


def validate_paired(root: Path, reporter: Reporter) -> None:
    required_dirs = ["train_A", "train_B", "test_A", "test_B"]
    for name in required_dirs:
        path = root / name
        if not path.is_dir():
            reporter.error(f"missing required paired directory: {path}")

    for split in ("train", "test"):
        captions_path = root / f"{split}_prompts.json"
        captions = load_json_object(captions_path, reporter, f"{split} prompt JSON")
        if captions is None:
            continue
        if not captions:
            reporter.error(f"{split} prompt JSON is empty: {captions_path}")
            continue

        split_a = root / f"{split}_A"
        split_b = root / f"{split}_B"
        keys = sorted(captions.keys())
        reporter.note(f"{split}: {len(keys)} prompt entries")

        for key in keys:
            value = captions[key]
            if unsafe_key(key):
                reporter.error(f"{split}: unsafe or empty prompt key {key!r}; use relative image filenames")
                continue
            if not isinstance(value, str):
                reporter.error(f"{split}: prompt for {key!r} is {type(value).__name__}, expected string")
            elif not value.strip():
                reporter.warn(f"{split}: prompt for {key!r} is empty after stripping whitespace")
            if Path(key).suffix.lower() not in COMMON_IMAGE_EXTS:
                reporter.warn(f"{split}: prompt key {key!r} has an uncommon image extension")

            a_path = split_a / key
            b_path = split_b / key
            if not a_path.is_file():
                reporter.error(f"{split}: prompt key {key!r} missing from {split}_A")
            if not b_path.is_file():
                reporter.error(f"{split}: prompt key {key!r} missing from {split}_B")

        key_set = set(keys)
        for side_name, side_dir in ((f"{split}_A", split_a), (f"{split}_B", split_b)):
            if side_dir.is_dir():
                all_files = sorted(p for p in side_dir.rglob("*") if p.is_file())
                if not all_files:
                    reporter.error(f"{side_name} is empty")
                image_files = recursive_common_images(side_dir)
                if not image_files:
                    reporter.warn(f"{side_name} contains no files with common lowercase image extensions")
                extras = [rel(p, side_dir) for p in image_files if rel(p, side_dir) not in key_set]
                if extras:
                    sample = ", ".join(extras[:5])
                    more = "" if len(extras) <= 5 else f" (+{len(extras) - 5} more)"
                    reporter.warn(f"{side_name}: image-like files not referenced by {split}_prompts.json: {sample}{more}")


def validate_fixed_prompt(root: Path, name: str, reporter: Reporter) -> None:
    path = root / name
    if not path.is_file():
        reporter.error(f"missing fixed prompt file: {path}")
        return
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        reporter.error(f"fixed prompt file is empty: {path}")
    else:
        reporter.note(f"{name}: {len(text)} characters")


def validate_unpaired(root: Path, reporter: Reporter) -> None:
    for name in ("train_A", "train_B", "test_A", "test_B"):
        path = root / name
        if not path.is_dir():
            reporter.error(f"missing required unpaired directory: {path}")

    validate_fixed_prompt(root, "fixed_prompt_a.txt", reporter)
    validate_fixed_prompt(root, "fixed_prompt_b.txt", reporter)

    checks = [
        ("train_A", UNPAIRED_TRAIN_EXTS, "training"),
        ("train_B", UNPAIRED_TRAIN_EXTS, "training"),
        ("test_A", UNPAIRED_VAL_EXTS, "validation"),
        ("test_B", UNPAIRED_VAL_EXTS, "validation"),
    ]
    for dirname, exts, purpose in checks:
        folder = root / dirname
        images = top_level_images(folder, exts)
        if folder.is_dir() and not images:
            reporter.error(
                f"{dirname} has no top-level {purpose} images matched by source globs "
                f"({', '.join('*' + e for e in exts)})"
            )
        else:
            reporter.note(f"{dirname}: {len(images)} matched {purpose} images")

        mismatched = files_with_case_mismatched_ext(folder, exts)
        if mismatched:
            sample = ", ".join(p.name for p in mismatched[:5])
            more = "" if len(mismatched) <= 5 else f" (+{len(mismatched) - 5} more)"
            reporter.warn(
                f"{dirname}: files with uppercase/mixed-case extensions are not matched by source lowercase globs: {sample}{more}"
            )

        if dirname.startswith("test"):
            gifs = top_level_images(folder, (".gif",))
            if gifs:
                sample = ", ".join(p.name for p in gifs[:5])
                more = "" if len(gifs) <= 5 else f" (+{len(gifs) - 5} more)"
                reporter.warn(f"{dirname}: GIF files are ignored by unpaired validation scans: {sample}{more}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate img2img-turbo paired or unpaired training dataset layout without model/tokenizer downloads."
    )
    parser.add_argument("--mode", choices=("paired", "unpaired"), required=True, help="Dataset contract to validate.")
    parser.add_argument("--dataset-folder", required=True, type=Path, help="Dataset root containing train/test domain folders.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.dataset_folder
    reporter = Reporter()

    print(f"Validation mode: {args.mode}")
    print(f"Dataset folder: {root}")

    if not root.exists():
        reporter.error(f"dataset folder does not exist: {root}")
    elif not root.is_dir():
        reporter.error(f"dataset folder is not a directory: {root}")
    else:
        if args.mode == "paired":
            validate_paired(root, reporter)
        else:
            validate_unpaired(root, reporter)

    if reporter.notes:
        print("\nNotes:")
        for msg in reporter.notes:
            print(f"  - {msg}")
    if reporter.warnings:
        print("\nWarnings:")
        for msg in reporter.warnings:
            print(f"  - {msg}")
    if reporter.errors:
        print("\nErrors:")
        for msg in reporter.errors:
            print(f"  - {msg}")
        print(f"\nRESULT: FAIL ({len(reporter.errors)} error(s), {len(reporter.warnings)} warning(s))")
        return 1

    print(f"\nRESULT: OK ({len(reporter.warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
