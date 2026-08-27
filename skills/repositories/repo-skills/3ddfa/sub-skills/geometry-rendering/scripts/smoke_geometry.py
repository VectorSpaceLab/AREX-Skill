#!/usr/bin/env python3
"""Smoke-test 3DDFA geometry reconstruction shapes.

This helper checks the canonical zero-vector path for sparse and dense
reconstruction without invoking the detector or renderer stack.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify sparse and dense reconstruct_vertex output shapes."
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help="Path to the 3DDFA repository root.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.expanduser().resolve()
    if not repo_root.is_dir():
        raise NotADirectoryError(f"repo root does not exist: {repo_root}")
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from utils.ddfa import reconstruct_vertex

    param = np.zeros(62, dtype=np.float32)
    sparse = reconstruct_vertex(param, dense=False)
    dense = reconstruct_vertex(param, dense=True)

    assert sparse.shape == (3, 68), f"unexpected sparse shape: {sparse.shape}"
    assert dense.shape == (3, 53215), f"unexpected dense shape: {dense.shape}"
    assert np.isfinite(sparse).all(), "sparse vertices contain non-finite values"
    assert np.isfinite(dense).all(), "dense vertices contain non-finite values"

    print(f"sparse shape: {sparse.shape}")
    print(f"dense shape: {dense.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
