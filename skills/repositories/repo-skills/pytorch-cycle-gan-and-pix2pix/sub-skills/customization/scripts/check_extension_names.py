#!/usr/bin/env python3
"""Check repository model/dataset filename and class-name conventions.

This helper only inspects text when --repo-root is supplied. It never imports
repository code, executes user modules, edits files, or accesses the network.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_CLASS_RE = re.compile(
    r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(([^)]*)\))?\s*:",
    re.MULTILINE,
)


def _normalize(value: str) -> str:
    """Match the registry's case-insensitive, underscore-free class key."""
    return re.sub(r"[_-]", "", value).lower()


def _pascal_token(token: str) -> str:
    """Pascal-case one token while keeping common vision/ML acronyms readable."""
    acronym_map = {
        "cpu": "CPU",
        "cuda": "CUDA",
        "ddp": "DDP",
        "fcn": "FCN",
        "gan": "GAN",
        "gpu": "GPU",
        "hed": "HED",
        "lab": "Lab",
        "rgb": "RGB",
    }
    lower = token.lower()
    if lower in acronym_map:
        return acronym_map[lower]
    pieces = re.findall(r"[A-Za-z]+|\d+", token)
    if not pieces:
        return token[:1].upper() + token[1:]
    return "".join(piece if piece.isdigit() else piece[:1].upper() + piece[1:].lower() for piece in pieces)


def _class_stem(name: str) -> str:
    """Return a readable PascalCase suggestion for a registry name."""
    parts = [part for part in re.split(r"[_-]+", name) if part]
    return "".join(_pascal_token(part) for part in parts)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print and optionally text-check a custom model or dataset name.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--kind",
        required=True,
        choices=("model", "dataset"),
        help="extension type to check",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="value passed to --model or --dataset_mode",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="optional repository root for a non-importing file/class text check",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    name = args.name.strip()
    if not name or not _NAME_RE.fullmatch(name):
        parser.error("--name must be a Python-module-safe identifier fragment: letters, digits, '_' and no leading digit")

    suffix = "Model" if args.kind == "model" else "Dataset"
    directory = "models" if args.kind == "model" else "data"
    filename = f"{name}_{args.kind}.py"
    class_name = f"{_class_stem(name)}{suffix}"
    registry_key = _normalize(name + suffix)
    relative_path = Path(directory) / filename

    print(f"kind: {args.kind}")
    print(f"name: {name}")
    print(f"expected file: {relative_path}")
    print(f"expected class: {class_name}")
    print(f"registry match key: {registry_key}")

    if args.repo_root is None:
        return 0

    root = args.repo_root.expanduser().resolve()
    target = root / relative_path
    if not target.is_file():
        print(f"ERROR: file not found: {target}", file=sys.stderr)
        return 1

    try:
        source = target.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: unable to read {target}: {exc}", file=sys.stderr)
        return 1

    matches = []
    for candidate, bases in _CLASS_RE.findall(source):
        if _normalize(candidate) == registry_key:
            matches.append((candidate, bases.strip()))

    if not matches:
        print(
            f"ERROR: no class matching registry key {registry_key!r} found in {target}",
            file=sys.stderr,
        )
        return 1

    found = ", ".join(candidate for candidate, _ in matches)
    print(f"OK: matching class text found: {found}")
    print("note: this check does not import the module or prove runtime inheritance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
