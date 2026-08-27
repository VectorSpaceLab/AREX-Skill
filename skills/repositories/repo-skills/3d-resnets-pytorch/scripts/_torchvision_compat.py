#!/usr/bin/env python3
"""Compatibility helpers for running the legacy 3D-ResNets-PyTorch CLI.

Modern torchvision releases no longer expose ``transforms.Scale``. The source
repository still imports it when loading ``spatial_transforms.py`` and
``main.py``. These helpers add a temporary alias to ``Resize`` so inspection
and CLI wrappers can still run against a modern environment.
"""

from __future__ import annotations

import sys
from pathlib import Path


def add_repo_root(repo_root: str | Path) -> Path:
    """Insert the repository root at the front of sys.path and return it."""

    repo_root = Path(repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return repo_root


def ensure_legacy_scale_alias() -> bool:
    """Add torchvision.transforms.transforms.Scale if the wheel no longer ships it.

    Returns True when the alias was added, False when the runtime already had a
    usable ``Scale`` symbol.
    """

    import torchvision.transforms as tvt
    import torchvision.transforms.transforms as tvtt

    if hasattr(tvtt, "Scale"):
        return False
    tvtt.Scale = tvt.Resize
    return True


def prepare_source_runtime(repo_root: str | Path, *, with_scale_shim: bool = True) -> bool:
    """Prepare a repo checkout for safe imports and CLI execution.

    Returns True if the temporary Scale alias was added.
    """

    add_repo_root(repo_root)
    if with_scale_shim:
        return ensure_legacy_scale_alias()
    return False
