#!/usr/bin/env python3
"""Smoke-check the ACT++ VINN offline stack.

The helper imports VINN modules from an explicit ACT++ checkout and verifies
that CUDA is visible. It does not cache features, choose k, or run real-robot
evaluation.

Example:
    python scripts/check_vinn_stack.py --repo-root /path/to/act-plus-plus
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def add_repo_root(repo_root: str) -> None:
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"repo root does not exist: {root}")
    sys.path.insert(0, str(root))


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check ACT++ VINN imports.")
    parser.add_argument("--repo-root", required=True, help="Path to an ACT++ checkout.")
    args = parser.parse_args()

    add_repo_root(args.repo_root)

    try:
        import torch
        import torchvision
        import vinn_cache_feature
        import vinn_select_k
        import vinn_eval
    except Exception as exc:
        print(f"IMPORT FAIL: {type(exc).__name__}: {exc}")
        return 1

    print(f"torch={torch.__version__}")
    print(f"torchvision={torchvision.__version__}")
    print(f"CUDA available={torch.cuda.is_available()}")
    print(f"CUDA device count={torch.cuda.device_count()}")
    print(f"vinn_cache_feature={vinn_cache_feature.__file__}")
    print(f"vinn_select_k={vinn_select_k.__file__}")
    print(f"vinn_eval={vinn_eval.__file__}")
    print(f"cache helper has chunks={hasattr(vinn_cache_feature, 'chunks')}")
    print(f"select helper has calculate_nearest_neighbors={hasattr(vinn_select_k, 'calculate_nearest_neighbors')}")

    if not torch.cuda.is_available():
        print("ERROR: VINN source workflows use .cuda() directly.")
        return 2

    print("VINN stack smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
