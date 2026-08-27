#!/usr/bin/env python3
"""Validate visual-anagram view names and optional per-view arguments.

This helper only checks view construction; it does not sample images or write
outputs.

Examples:
    python check_views.py --repo-root /path/to/checkout --view identity flip --view-args '' ''
    python check_views.py --repo-root /path/to/checkout --view patch_permute --view-args 8
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--view", nargs="+", required=True)
    parser.add_argument("--view-args", nargs="*", default=None)
    args = parser.parse_args()

    if args.repo_root is not None:
        repo_root = args.repo_root.resolve()
        sys.path.insert(0, str(repo_root))
        visual_root = repo_root / "visual_anagrams"
        if visual_root.exists():
            sys.path.insert(0, str(visual_root))
        print(f"repo_root={repo_root}")

    try:
        from visual_anagrams.views import get_anagrams_views
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: could not import get_anagrams_views ({type(exc).__name__}: {exc})")
        return 1

    view_args = args.view_args
    if view_args is not None and len(view_args) not in (0, len(args.view)):
        print("FAIL: when provided, --view-args must have the same number of entries as --view")
        return 1

    try:
        views = get_anagrams_views(args.view, view_args=view_args)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: could not build views ({type(exc).__name__}: {exc})")
        return 1

    print(f"views={len(views)}")
    for idx, view in enumerate(views):
        print(f"  {idx}: {view.__class__.__name__}")
    print("Result: view selection looks valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
