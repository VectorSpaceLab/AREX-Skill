#!/usr/bin/env python3
"""Validate common dataset layouts used by the Cream monorepo.

The checker is read-only. It does not download data or copy files.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def _check_dir(path: Path) -> bool:
    return path.exists() and path.is_dir()


def _check_file(path: Path) -> bool:
    return path.exists() and path.is_file()


def check_imagenet1k(root: Path) -> list[str]:
    problems: list[str] = []
    train = root / "train"
    val = root / "val"
    train_tar = root / "train.tar"
    val_tar = root / "val.tar"
    if not (_check_dir(train) or _check_file(train_tar)):
        problems.append("missing train/ directory or train.tar archive")
    if not (_check_dir(val) or _check_file(val_tar)):
        problems.append("missing val/ directory or val.tar archive")
    return problems


def check_imagenet22k(root: Path) -> list[str]:
    problems: list[str] = []
    if not _check_file(root / "in22k_image_names.txt"):
        problems.append("missing in22k_image_names.txt")
    if not any(child.suffix == ".zip" for child in root.iterdir() if child.is_file()):
        problems.append("no .zip class archives found")
    return problems


def check_subimagenet(root: Path) -> list[str]:
    problems: list[str] = []
    subroot = root / "subImageNet"
    if not _check_dir(root / "train"):
        problems.append("missing source train/ directory")
    if not _check_dir(subroot):
        problems.append("missing subImageNet/ directory")
    else:
        if not _check_file(subroot / "info.txt"):
            problems.append("missing subImageNet/info.txt")
        if not _check_file(subroot / "subimages_list.txt"):
            problems.append("missing subImageNet/subimages_list.txt")
    return problems


def check_coco2017(root: Path) -> list[str]:
    problems: list[str] = []
    required = [root / "annotations", root / "train2017", root / "val2017"]
    missing = [str(path.name) for path in required if not _check_dir(path)]
    if missing:
        problems.append("missing directories: " + ", ".join(missing))
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate common dataset layouts")
    parser.add_argument("--root", required=True, help="Dataset root to inspect")
    parser.add_argument(
        "--kind",
        required=True,
        choices=["imagenet1k", "imagenet22k", "subimagenet", "coco2017"],
        help="Layout family to check.",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        print(f"ERROR: root does not exist: {root}")
        return 1

    if args.kind == "imagenet1k":
        problems = check_imagenet1k(root)
    elif args.kind == "imagenet22k":
        problems = check_imagenet22k(root)
    elif args.kind == "subimagenet":
        problems = check_subimagenet(root)
    else:
        problems = check_coco2017(root)

    if problems:
        print(f"FAIL: {args.kind} layout problems under {root}")
        for item in problems:
            print(f"- {item}")
        return 1

    print(f"OK: {args.kind} layout looks valid under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
