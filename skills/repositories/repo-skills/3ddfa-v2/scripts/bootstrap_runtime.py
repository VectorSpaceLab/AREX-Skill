"""Shared bootstrap helpers for bundled 3DDFA_V2 scripts.

These helpers keep the generated skill self-contained by resolving the repo
root, restoring deprecated NumPy aliases used by the legacy source tree, and
forcing a headless plotting backend unless the caller overrides it.
"""

from __future__ import annotations

import os
import runpy
import sys
import warnings
from pathlib import Path
from typing import Iterable

_NUMPY_ALIAS_MAP = {
    "long": int,
    "int": int,
    "float": float,
    "bool": bool,
    "object": object,
    "str": str,
}


def apply_numpy_compat() -> None:
    """Restore deprecated NumPy aliases expected by the repo source tree."""
    import numpy as np

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        for name, value in _NUMPY_ALIAS_MAP.items():
            if not hasattr(np, name):
                setattr(np, name, value)


def ensure_repo_root(repo_root: str | Path) -> Path:
    """Resolve the repo root, add it to ``sys.path``, and switch into it."""
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"repo root not found: {root}")

    os.environ.setdefault("MPLBACKEND", "Agg")
    apply_numpy_compat()

    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    os.chdir(root)
    return root


def run_module_as_main(module_name: str, forwarded_args: Iterable[str], repo_root: str | Path) -> None:
    """Run a repo module the same way ``python -m`` would.

    The helper sets ``sys.argv`` so the wrapped module keeps its original CLI.
    """
    ensure_repo_root(repo_root)
    forwarded = list(forwarded_args)
    sys.argv = [module_name.rsplit(".", 1)[-1] + ".py", *forwarded]
    runpy.run_module(module_name, run_name="__main__")
