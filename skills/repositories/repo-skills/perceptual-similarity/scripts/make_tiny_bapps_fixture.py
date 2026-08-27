#!/usr/bin/env python3
"""Create a tiny BAPPS-style smoke fixture from the bundled example assets.

The fixture is safe, deterministic, and self-contained. It copies the bundled
sample images into a BAPPS directory layout and writes one-label `.npy` files
for the 2AFC and JND smoke splits.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import numpy as np


SKILL_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = SKILL_ROOT / "assets" / "examples"


def copy_file(src: Path, dst: Path, *, overwrite: bool = True) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not overwrite:
        return
    shutil.copy2(src, dst)


def make_2afc_split(split_root: Path, *, overwrite: bool = True) -> None:
    src_ref = EXAMPLES / "ex_ref.png"
    src_p0 = EXAMPLES / "ex_p0.png"
    src_p1 = EXAMPLES / "ex_p1.png"
    for subdir in ["ref", "p0", "p1", "judge"]:
        (split_root / subdir).mkdir(parents=True, exist_ok=True)
    copy_file(src_ref, split_root / "ref" / "000.png", overwrite=overwrite)
    copy_file(src_p0, split_root / "p0" / "000.png", overwrite=overwrite)
    copy_file(src_p1, split_root / "p1" / "000.png", overwrite=overwrite)
    np.save(split_root / "judge" / "000.npy", np.array(1.0, dtype=np.float32))


def make_jnd_split(split_root: Path, *, overwrite: bool = True) -> None:
    src_p0 = EXAMPLES / "ex_ref.png"
    src_p1 = EXAMPLES / "ex_p1.png"
    for subdir in ["p0", "p1", "same"]:
        (split_root / subdir).mkdir(parents=True, exist_ok=True)
    copy_file(src_p0, split_root / "p0" / "000.png", overwrite=overwrite)
    copy_file(src_p1, split_root / "p1" / "000.png", overwrite=overwrite)
    np.save(split_root / "same" / "000.npy", np.array(1.0, dtype=np.float32))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a tiny BAPPS-style fixture from bundled example assets.")
    parser.add_argument("--output-root", type=Path, required=True, help="Fixture root to create.")
    parser.add_argument("--dataset-name", default="tiny", help="Split name to create inside each BAPPS branch.")
    parser.add_argument("--mode", choices=["both", "2afc", "jnd"], default="both", help="Which fixture branches to create.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files if they already exist.")
    args = parser.parse_args(argv)

    dataset_root = args.output_root / "dataset"
    if args.mode in {"both", "2afc"}:
        make_2afc_split(dataset_root / "2afc" / args.dataset_name, overwrite=args.overwrite)
    if args.mode in {"both", "jnd"}:
        make_jnd_split(dataset_root / "jnd" / args.dataset_name, overwrite=args.overwrite)

    print(f"Created tiny BAPPS fixture under {dataset_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
