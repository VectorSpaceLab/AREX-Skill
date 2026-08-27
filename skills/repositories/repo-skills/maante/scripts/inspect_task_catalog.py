#!/usr/bin/env python3
"""Inspect MaaNTE task JSON and interface imports without launching Maa.

Example:
    python scripts/inspect_task_catalog.py --repo-root /path/to/MaaNTE
    python scripts/inspect_task_catalog.py --repo-root . --json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def strip_jsonc(text: str) -> str:
    """Remove // and /* */ comments while preserving string content."""
    out: list[str] = []
    i = 0
    in_str = False
    esc = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def load_json_or_jsonc(path: Path) -> Any:
    return json.loads(strip_jsonc(path.read_text(encoding="utf-8")))


def collect(repo_root: Path) -> dict[str, Any]:
    interface_path = repo_root / "assets" / "interface.json"
    tasks_dir = repo_root / "assets" / "resource" / "tasks"
    pipeline_dir = repo_root / "assets" / "resource" / "base" / "pipeline"
    interface = load_json_or_jsonc(interface_path)
    imports = [str(x) for x in interface.get("import", [])]
    task_files = sorted(path for path in tasks_dir.rglob("*.json") if path.is_file())
    task_file_by_resource = {
        "resource/tasks/" + str(path.relative_to(tasks_dir)).replace("\\", "/"): path
        for path in task_files
    }

    imported_missing = [entry for entry in imports if entry.startswith("resource/tasks/") and entry not in task_file_by_resource]
    not_imported = [rel for rel in task_file_by_resource if rel not in imports]

    tasks = []
    option_refs = []
    for rel, path in task_file_by_resource.items():
        data = load_json_or_jsonc(path)
        options = data.get("option") or {}
        for task in data.get("task") or []:
            refs = task.get("option") or []
            missing_options = [name for name in refs if name not in options]
            tasks.append(
                {
                    "file": rel,
                    "name": task.get("name"),
                    "entry": task.get("entry"),
                    "controller": task.get("controller") or ["Any"],
                    "group": task.get("group") or [],
                    "options": refs,
                    "missing_options": missing_options,
                }
            )
            option_refs.extend((rel, task.get("name"), name) for name in refs)

    pipeline_files = sorted(str(path.relative_to(pipeline_dir)).replace("\\", "/") for path in pipeline_dir.rglob("*.json")) if pipeline_dir.exists() else []
    return {
        "interface_version": interface.get("version"),
        "controller_names": [item.get("name") for item in interface.get("controller", [])],
        "import_count": len(imports),
        "task_file_count": len(task_files),
        "pipeline_file_count": len(pipeline_files),
        "imported_missing": imported_missing,
        "not_imported": not_imported,
        "tasks": tasks,
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"Interface version: {report.get('interface_version')}")
    print("Controllers: " + ", ".join(str(x) for x in report.get("controller_names", [])))
    print(f"Imports: {report['import_count']} | task files: {report['task_file_count']} | pipeline files: {report['pipeline_file_count']}")
    if report["imported_missing"]:
        print("Missing imported task files:")
        for item in report["imported_missing"]:
            print(f"  - {item}")
    if report["not_imported"]:
        print("Task files not imported by interface.json:")
        for item in report["not_imported"]:
            print(f"  - {item}")
    print("Tasks:")
    for task in report["tasks"]:
        ctrl = ",".join(task["controller"])
        opts = ",".join(task["options"]) if task["options"] else "-"
        print(f"  - {task['name']} | entry={task['entry']} | controller={ctrl} | options={opts} | file={task['file']}")
        if task["missing_options"]:
            print("    missing option definitions: " + ", ".join(task["missing_options"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = parser.parse_args(argv)
    report = collect(args.repo_root.resolve())
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_text(report)
    errors = len(report["imported_missing"]) + sum(len(task["missing_options"]) for task in report["tasks"])
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
