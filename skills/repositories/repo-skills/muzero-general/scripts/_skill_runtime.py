#!/usr/bin/env python3
"""Shared path helpers for the self-contained MuZero General skill runtime."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Iterable, Optional, Tuple


class RuntimeSourceError(RuntimeError):
    """User-facing failure while resolving the bundled MuZero source."""


REQUIRED_SOURCE_MARKERS = ("muzero.py", "models.py", "self_play.py", "games")


def find_skill_root(start: Optional[Path] = None) -> Path:
    """Find the `muzero-general` skill root from a script path or cwd."""
    base = (start or Path(__file__)).expanduser().resolve()
    candidates = [base] if base.is_dir() else [base.parent]
    candidates.extend(candidates[0].parents)
    for candidate in candidates:
        if (candidate / "SKILL.md").is_file() and (candidate / "runtime" / "source" / "muzero.py").is_file():
            return candidate
    raise RuntimeSourceError(
        "Could not locate the muzero-general skill root containing SKILL.md and runtime/source/muzero.py"
    )


def bundled_source_root(start: Optional[Path] = None) -> Path:
    """Return the bundled MuZero General source snapshot path."""
    return find_skill_root(start) / "runtime" / "source"


def validate_source_root(repo_root: Path, required_markers: Iterable[str] = REQUIRED_SOURCE_MARKERS) -> Path:
    """Validate a MuZero General source root and return its resolved path."""
    root = repo_root.expanduser().resolve()
    missing = []
    for marker in required_markers:
        path = root / marker
        if not path.exists():
            missing.append(marker)
    if missing:
        raise RuntimeSourceError(
            f"MuZero General source root is missing {missing}; got {root}"
        )
    return root


def resolve_source_root(
    repo_root: Optional[Path],
    *,
    start: Optional[Path] = None,
    required_markers: Iterable[str] = REQUIRED_SOURCE_MARKERS,
) -> Tuple[Path, str]:
    """Resolve an optional user source root or the bundled source snapshot.

    Returns `(path, source_kind)` where `source_kind` is `bundled` or `external`.
    """
    if repo_root is None:
        return validate_source_root(bundled_source_root(start), required_markers), "bundled"
    return validate_source_root(repo_root, required_markers), "external"


def add_source_to_syspath(source_root: Path) -> None:
    """Prepend the source root to sys.path and PYTHONPATH.

    Ray worker processes import MuZero actor classes in separate Python workers,
    so updating only the driver process's `sys.path` is not enough. Keeping
    `PYTHONPATH` synchronized makes bundled modules such as `models` importable
    to Ray actors without requiring the current working directory to be a source
    checkout.
    """
    source = str(source_root)
    sys.path[:] = [entry for entry in sys.path if Path(entry or ".").resolve() != source_root]
    sys.path.insert(0, source)

    existing = [entry for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep) if entry]
    existing = [entry for entry in existing if Path(entry).expanduser().resolve() != source_root]
    os.environ["PYTHONPATH"] = os.pathsep.join([source] + existing)


def copy_bundled_source(destination: Path, *, overwrite: bool = False, start: Optional[Path] = None) -> Path:
    """Copy the bundled source snapshot to an editable destination directory."""
    source = bundled_source_root(start)
    dest = destination.expanduser().resolve()
    if dest.exists():
        if not overwrite:
            raise RuntimeSourceError(f"destination already exists: {dest}")
        if not dest.is_dir():
            raise RuntimeSourceError(f"destination exists and is not a directory: {dest}")
        shutil.rmtree(dest)
    shutil.copytree(
        source,
        dest,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    return validate_source_root(dest)
