#!/usr/bin/env python3
"""Inspect OFA model/task/criterion registration without running training.

This helper imports the repo root and local fairseq fork, then reports which
OFA tasks, models, and criteria are available. It is safe to run as a quick
registry check before composing prompt-tuning, adapter, or encouraging-loss
commands.

Example:
  python inspect_ofa_registration.py --repo-root /path/to/OFA
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Dict, List


def _prepend_repo_paths(repo_root: Path) -> None:
    repo_root = repo_root.resolve()
    sys.path.insert(0, str(repo_root))
    fairseq_dir = repo_root / "fairseq"
    if fairseq_dir.exists():
        sys.path.insert(1, str(fairseq_dir))


def _collect_registered(module_name: str, attr_name: str) -> List[str]:
    module = importlib.import_module(module_name)
    attr = getattr(module, attr_name, None)
    if attr is None:
        return []
    if isinstance(attr, dict):
        return sorted(attr.keys())
    try:
        return sorted(list(attr))
    except TypeError:
        return [str(attr)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    _prepend_repo_paths(args.repo_root)

    # Import side-effect modules that register tasks/models/criteria.
    for module_name in ["ofa_module", "models", "tasks", "criterions"]:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            print(f"error: failed to import {module_name}: {type(exc).__name__}: {exc}")
            return 1

    from fairseq.tasks import TASK_REGISTRY
    from fairseq.models import MODEL_REGISTRY, ARCH_MODEL_REGISTRY
    from fairseq.criterions import CRITERION_REGISTRY

    print("tasks:")
    for name in sorted(TASK_REGISTRY.keys()):
        print(f"  - {name}")
    print("models:")
    for name in sorted(MODEL_REGISTRY.keys()):
        print(f"  - {name}")
    print("architectures:")
    for name in sorted(ARCH_MODEL_REGISTRY.keys()):
        print(f"  - {name}")
    print("criteria:")
    for name in sorted(CRITERION_REGISTRY.keys()):
        print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
