#!/usr/bin/env python3
"""Check whether a Wren project meets framework SDK prerequisites.

Usage:
  python sdk_project_probe.py --project ./analytics-project
  python sdk_project_probe.py --project ./analytics-project --instantiate
"""
from __future__ import annotations

import argparse
import importlib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument(
        "--instantiate",
        action="store_true",
        help="construct available toolkit objects; does not run a query",
    )
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    failures: list[str] = []
    for path in (project / "wren_project.yml", project / "target" / "mdl.json"):
        if not path.is_file():
            failures.append(f"missing required project file: {path.name if path.parent == project else 'target/mdl.json'}")

    available = []
    for module in ("wren_langchain", "wren_pydantic"):
        try:
            importlib.import_module(module)
            available.append(module)
            print(f"import {module}: OK")
        except Exception as exc:
            print(f"import {module}: unavailable ({type(exc).__name__}: {exc})")

    memory_dir = project / ".wren" / "memory"
    print(f"memory state: {'present' if memory_dir.is_dir() else 'absent'}")
    if args.instantiate and not failures:
        for module, attr in (("wren_langchain", "WrenToolkit"), ("wren_pydantic", "WrenToolkit")):
            if module not in available:
                continue
            try:
                toolkit = getattr(importlib.import_module(module), attr).from_project(project)
                print(f"{module}.WrenToolkit.from_project: OK ({type(toolkit).__name__})")
            except Exception as exc:
                failures.append(f"{module} toolkit initialization: {type(exc).__name__}: {exc}")

    if failures:
        print("Problems:")
        print("\n".join(f"- {item}" for item in failures))
        return 1
    print("Project prerequisites passed. No live database query was run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
