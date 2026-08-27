#!/usr/bin/env python3
"""Inspect Wren knowledge and derived-memory state without importing LanceDB.

Usage:
  python inspect_memory_state.py --project ./analytics-project
"""
from __future__ import annotations

import argparse
from pathlib import Path


def count_files(path: Path, suffix: str | None = None) -> int:
    if not path.is_dir():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file() and (suffix is None or item.suffix == suffix))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    if not (project / "wren_project.yml").is_file():
        print(f"Not a Wren project: {project}")
        return 1

    knowledge = project / "knowledge"
    pairs = knowledge / "sql"
    memory = project / ".wren" / "memory"
    print(f"Knowledge directory: {'present' if knowledge.is_dir() else 'missing'}")
    print(f"Rules files: {count_files(knowledge / 'rules', '.md')}")
    print(f"NL-to-SQL pair files: {count_files(pairs, '.md')}")
    print(f"Derived memory directory: {'present' if memory.is_dir() else 'absent'}")
    if memory.is_dir():
        print(f"Derived-memory files: {count_files(memory)}")
        print("Next: wren memory status && wren memory check")
    else:
        print("Next: wren memory recall -q '...' works over pair files; install wrenai[memory] for semantic fetch/index.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
