#!/usr/bin/env python3
"""Validate the Office-31 or Office-Home split files, image root, and bundled runtime package."""

from __future__ import annotations

import argparse
from importlib import resources
from pathlib import Path
import sys

OFFICE_RUNTIME_SRC = Path(__file__).resolve().parent / "office_runtime" / "src"
if OFFICE_RUNTIME_SRC.is_dir() and str(OFFICE_RUNTIME_SRC) not in sys.path:
    sys.path.insert(0, str(OFFICE_RUNTIME_SRC))


TASKS = {
    "office-31": ["amazon", "dslr", "webcam"],
    "office-home": ["Art", "Clipart", "Product", "Real_World"],
}


def _split_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "references" / "data_txt"


def _package_split_dir(dataset: str):
    return resources.files("libmtl_office_benchmark").joinpath("data_txt", dataset)


def _count_lines(path) -> int:
    with path.open("r", encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip())


def _check_split_tree(split_root: Path, dataset: str, image_root: Path) -> None:
    if not split_root.is_dir():
        raise SystemExit(f"missing bundled split directory: {split_root}")

    missing = []
    for task in TASKS[dataset]:
        for mode in ["train", "val", "test"]:
            split_file = split_root / f"{task}_{mode}.txt"
            if not split_file.is_file():
                missing.append(split_file.name)
                continue
            lines = [line.strip() for line in split_file.open("r", encoding="utf-8") if line.strip()]
            print(f"{split_file.name}: {len(lines)} entries")
            if not lines:
                missing.append(split_file.name)
                continue
            for line in lines[:3]:
                rel_path, *_ = line.split()
                if not (image_root / rel_path).is_file():
                    raise SystemExit(f"missing image referenced by {split_file.name}: {rel_path}")

    if missing:
        raise SystemExit(f"missing or empty split files: {', '.join(missing)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the office benchmark layout")
    parser.add_argument("dataset", choices=sorted(TASKS), help="dataset family")
    parser.add_argument("image_root", type=Path, help="path to the raw image root")
    parser.add_argument(
        "--check-runtime-package",
        action="store_true",
        help="also verify the bundled installable office runtime package data",
    )
    args = parser.parse_args()

    root = args.image_root.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"missing image root: {root}")

    _check_split_tree(_split_dir() / args.dataset, args.dataset, root)
    print(f"office data layout: ok ({args.dataset})")

    if args.check_runtime_package:
        pkg_split_root = _package_split_dir(args.dataset)
        try:
            package_name = pkg_split_root.name
        except Exception:
            package_name = args.dataset
        _check_split_tree(Path(pkg_split_root), args.dataset, root)
        print(f"office runtime package data: ok ({package_name})")


if __name__ == "__main__":
    main()
