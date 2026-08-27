#!/usr/bin/env python3
"""Check whether a ComfyUI extension checkout looks discoverable.

This helper is safe to run. It does not mutate the repository or the ComfyUI
checkout; it only inspects filesystem layout and reports likely discovery
issues.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check the filesystem layout for the Save As Script extension."
    )
    parser.add_argument(
        "--extension-root",
        type=Path,
        default=Path.cwd(),
        help="Path to the ComfyUI-to-Python-Extension checkout.",
    )
    parser.add_argument(
        "--comfyui-root",
        type=Path,
        help="Optional ComfyUI checkout to compare against custom_nodes discovery.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.extension_root

    required = [root / "__init__.py", root / "js" / "save-as-script.js", root / "pyproject.toml"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print("missing:")
        for path in missing:
            print(f"  - {path}")
        return 1

    print("extension-root-ok")
    print(f"extension-root={root}")

    if args.comfyui_root is not None:
        custom_nodes = args.comfyui_root / "custom_nodes"
        candidate = custom_nodes / root.name
        if candidate.exists():
            print(f"discoverable-through-custom_nodes={candidate}")
        else:
            print(f"not-linked-under-custom_nodes={candidate}")
        if not custom_nodes.exists():
            print(f"missing-custom_nodes-dir={custom_nodes}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
