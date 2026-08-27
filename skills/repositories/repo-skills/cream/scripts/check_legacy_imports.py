#!/usr/bin/env python3
"""Check legacy NAS modules under a modern-torch compatibility shim.

The original AutoFormer / Cream / CDARTS code expects `torch._six`, which was
removed in modern torch releases. This helper injects a tiny compatibility
module in-process and imports the stable config / utility surfaces that are
useful for skill inspection.
"""

from __future__ import annotations

import argparse
import collections.abc
import importlib
import inspect
import sys
import types
from pathlib import Path


DEFAULT_MODULES = [
    "AutoFormer.model.utils",
    "AutoFormer.lib.config",
    "Cream.lib.config",
    "CDARTS.lib.config",
]


def _install_torch_six_shim() -> None:
    shim = types.ModuleType("torch._six")
    shim.container_abcs = collections.abc
    sys.modules.setdefault("torch._six", shim)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check legacy NAS imports")
    parser.add_argument("--repo-root", required=True, help="Path to a Cream checkout")
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        help="Additional dotted module names to import after the shim is installed.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"ERROR: repo root does not exist: {repo_root}")
        return 1

    for rel in ["AutoFormer", "Cream", "CDARTS"]:
        candidate = repo_root / rel
        if candidate.exists():
            sys.path.insert(0, str(candidate))

    _install_torch_six_shim()

    ok = True
    for name in DEFAULT_MODULES + list(args.module):
        try:
            module = importlib.import_module(name)
            summary = getattr(module, "__file__", "") or "<module>"
            print(f"{name}: ok -> {summary}")
            if hasattr(module, "update_config_from_file"):
                print(f"{name}: update_config_from_file{inspect.signature(module.update_config_from_file)}")
            if hasattr(module, "get_parser"):
                print(f"{name}: get_parser{inspect.signature(module.get_parser)}")
            if hasattr(module, "SearchConfig"):
                print(f"{name}: SearchConfig available")
            if hasattr(module, "AugmentConfig"):
                print(f"{name}: AugmentConfig available")
        except Exception as exc:  # pragma: no cover - diagnostic path
            print(f"{name}: error -> {type(exc).__name__}: {exc}")
            ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
