#!/usr/bin/env python3
"""Validate Meshroom node descriptor classes in a Python module without computing them."""

from __future__ import annotations

import argparse
import importlib.util
import inspect
from pathlib import Path
import sys


def loadModule(path: Path):
    moduleName = f"meshroom_skill_descriptor_{path.stem}"
    spec = importlib.util.spec_from_file_location(moduleName, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[moduleName] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Meshroom BaseNode descriptors in a Python module.")
    parser.add_argument("module", type=Path, help="Python file containing one or more desc.BaseNode subclasses.")
    parser.add_argument("--repo-root", help="Optional source checkout root to add to sys.path before import.")
    args = parser.parse_args()

    if args.repo_root:
        sys.path.insert(0, str(Path(args.repo_root).resolve()))
    modulePath = args.module.resolve()
    if not modulePath.is_file():
        print(f"module not found: {modulePath}", file=sys.stderr)
        return 2

    from meshroom.core import desc
    from meshroom.core.plugins.base import NodeDescProvider, NodeDescProviderStatus

    module = loadModule(modulePath)
    classes = [
        value
        for _, value in inspect.getmembers(module, inspect.isclass)
        if issubclass(value, desc.BaseNode) and value is not desc.BaseNode and value.__module__ == module.__name__
    ]
    if not classes:
        print("no desc.BaseNode subclasses found", file=sys.stderr)
        return 1

    exitCode = 0
    for nodeClass in classes:
        provider = NodeDescProvider(nodeClass)
        print(f"{nodeClass.__name__}: {provider.status.name}")
        for error in provider.errors:
            print(f"  - {NodeDescProvider.formatNodeDescriptionErrorMessage(error)}")
        if provider.status in (NodeDescProviderStatus.DESC_ERROR, NodeDescProviderStatus.ERROR):
            exitCode = 1
    return exitCode


if __name__ == "__main__":
    raise SystemExit(main())
