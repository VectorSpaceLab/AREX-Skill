#!/usr/bin/env python3
"""Read-only completeness check for one FlashVSR v1/v1.1 model directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# The upstream README lists four tensor artifacts plus README.md.
EXPECTED_FILES = (
    "diffusion_pytorch_model_streaming_dmd.safetensors",
    "Wan2.1_VAE.pth",
    "LQ_proj_in.ckpt",
    "TCDecoder.ckpt",
    "README.md",
)
LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check the five documented FlashVSR bundle files for existence, "
            "non-zero size, and unresolved Git LFS pointers. No downloads."
        )
    )
    parser.add_argument("model_dir", type=Path, help="Local v1 or v1.1 model directory")
    parser.add_argument(
        "--version", choices=("v1", "v1.1"), default=None,
        help="Optional label shown in the summary; it does not change filenames.",
    )
    return parser.parse_args()


def check_file(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, "missing"
    try:
        size = path.stat().st_size
        if size == 0:
            return False, "empty"
        with path.open("rb") as handle:
            prefix = handle.read(len(LFS_POINTER_PREFIX))
    except OSError as exc:
        return False, f"unreadable ({type(exc).__name__})"
    if prefix == LFS_POINTER_PREFIX:
        return False, "Git LFS pointer (content not fetched)"
    return True, f"ok ({size} bytes)"


def main() -> int:
    args = parse_args()
    root = args.model_dir
    label = f" {args.version}" if args.version else ""
    print(f"FlashVSR bundle{label}: {root.name or root}")
    failed = False
    for filename in EXPECTED_FILES:
        ok, detail = check_file(root / filename)
        print(f"{'OK  ' if ok else 'FAIL'} {filename}: {detail}")
        failed |= not ok
    if failed:
        print("Result: incomplete bundle; no downloads were attempted.")
        return 1
    print("Result: five-file bundle is present and non-empty.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
