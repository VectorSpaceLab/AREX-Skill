#!/usr/bin/env python3
"""Inspect the pyAudioAnalysis legacy CLI without running an analysis task.

The pyAudioAnalysis 0.3.x CLI lives in audioAnalysis.py and uses legacy
sibling imports. This helper locates the installed package, adds the package
folder to sys.path for subprocess help calls, and prints task names/help.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Dict, Iterable, List, Tuple


TaskInfo = Dict[str, object]


def locate_package() -> Tuple[Path, Path]:
    """Return (package_dir, audioAnalysis.py path) for installed pyAudioAnalysis."""
    spec = importlib.util.find_spec("pyAudioAnalysis")
    if spec is None or spec.origin is None:
        raise SystemExit(
            "pyAudioAnalysis is not importable in this Python environment. "
            "Install pyAudioAnalysis before inspecting its CLI."
        )
    package_dir = Path(spec.origin).resolve().parent
    script = package_dir / "audioAnalysis.py"
    if not script.is_file():
        raise SystemExit(
            "The importable pyAudioAnalysis package does not contain "
            "audioAnalysis.py. The legacy CLI may be unavailable."
        )
    if str(package_dir) not in sys.path:
        # The legacy script imports siblings such as ShortTermFeatures by their
        # top-level names, so the package directory itself must be importable.
        sys.path.insert(0, str(package_dir))
    return package_dir, script


def _collect_statement(lines: List[str], start: int) -> Tuple[str, int]:
    stmt_lines: List[str] = []
    balance = 0
    saw_open = False
    i = start
    while i < len(lines):
        line = lines[i]
        stmt_lines.append(line)
        balance += line.count("(") - line.count(")")
        saw_open = saw_open or "(" in line
        if saw_open and balance <= 0:
            return "\n".join(stmt_lines), i + 1
        i += 1
    return "\n".join(stmt_lines), i


def _extract_first_string_after(text: str, marker: str) -> str:
    m = re.search(re.escape(marker) + r"\s*\(\s*(['\"])(.*?)\1", text, re.S)
    return m.group(2) if m else ""


def _extract_string_literals(text: str) -> List[str]:
    return [m.group(2) for m in re.finditer(r"(['\"])(.*?)(?<!\\)\1", text, re.S)]


def _extract_choices(stmt: str) -> List[str]:
    m = re.search(r"choices\s*=\s*\[(.*?)\]", stmt, re.S)
    if not m:
        return []
    return [s for s in _extract_string_literals(m.group(1)) if not s.startswith("-")]


def _extract_default(stmt: str) -> str:
    m = re.search(r"default\s*=\s*([^,\)\n]+)", stmt)
    return m.group(1).strip() if m else ""


def _extract_nargs(stmt: str) -> str:
    m = re.search(r"nargs\s*=\s*([^,\)\n]+)", stmt)
    return m.group(1).strip().strip("'\"") if m else ""


def extract_tasks(script: Path) -> List[TaskInfo]:
    """Derive subcommands and flag summaries from audioAnalysis.py source."""
    try:
        text = script.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = script.read_text(errors="replace")

    lines = text.splitlines()
    parser_vars: Dict[str, TaskInfo] = {}
    order: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "= tasks.add_parser" in line:
            stmt, i = _collect_statement(lines, i)
            lhs = stmt.split("=", 1)[0].strip()
            task_name = _extract_first_string_after(stmt, "add_parser")
            if task_name:
                parser_vars[lhs] = {"name": task_name, "flags": []}
                order.append(lhs)
            continue
        if ".add_argument" in line:
            stmt, i = _collect_statement(lines, i)
            var = stmt.split(".add_argument", 1)[0].strip()
            if var in parser_vars:
                flags = [s for s in _extract_string_literals(stmt) if s.startswith("-")]
                if flags:
                    item = {
                        "flags": flags,
                        "required": "required=True" in stmt.replace(" ", ""),
                        "store_true": "store_true" in stmt,
                        "choices": _extract_choices(stmt),
                        "default": _extract_default(stmt),
                        "nargs": _extract_nargs(stmt),
                    }
                    parser_vars[var]["flags"].append(item)  # type: ignore[index]
            continue
        if "return parser.parse_args" in line:
            break
        i += 1
    return [parser_vars[var] for var in order]


def print_task_summary(tasks: Iterable[TaskInfo]) -> None:
    print("\n== Source-derived subcommand summary ==")
    for task in tasks:
        print(f"\n{task['name']}")
        flags = task.get("flags") or []
        if not flags:
            print("  (no flags recorded)")
            continue
        for flag in flags:  # type: ignore[assignment]
            pieces = [", ".join(flag["flags"])]
            if flag.get("required"):
                pieces.append("required")
            if flag.get("store_true"):
                pieces.append("flag")
            if flag.get("nargs"):
                pieces.append(f"nargs={flag['nargs']}")
            if flag.get("choices"):
                pieces.append("choices=" + "|".join(flag["choices"]))
            if flag.get("default"):
                pieces.append("default=" + flag["default"])
            print("  - " + "; ".join(pieces))


def scrub_paths(text: str, package_dir: Path) -> str:
    """Avoid dumping local installation paths in ordinary error output."""
    replacements = [package_dir, package_dir.parent]
    cleaned = text
    for path in sorted({str(p) for p in replacements}, key=len, reverse=True):
        cleaned = cleaned.replace(path, "<pyAudioAnalysis-package>")
    return cleaned


def run_help(script: Path, package_dir: Path, task: str | None, timeout: float) -> int:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(package_dir) + (os.pathsep + existing if existing else "")
    cmd = [sys.executable, str(script)]
    if task:
        cmd.extend([task, "--help"])
    else:
        cmd.append("--help")
    try:
        completed = subprocess.run(
            cmd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"Help command timed out after {timeout:g}s; no analysis task was run.")
        return 124

    if completed.stdout:
        print(scrub_paths(completed.stdout.rstrip(), package_dir))
    if completed.returncode != 0:
        print("\nHelp execution failed; stderr follows with local paths scrubbed:", file=sys.stderr)
        if completed.stderr:
            print(scrub_paths(completed.stderr.rstrip(), package_dir), file=sys.stderr)
        return completed.returncode
    if completed.stderr:
        print(scrub_paths(completed.stderr.rstrip(), package_dir), file=sys.stderr)
    return 0


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Locate the installed pyAudioAnalysis package and inspect the "
            "legacy audioAnalysis.py CLI without running analysis tasks."
        )
    )
    parser.add_argument(
        "--task",
        action="append",
        default=[],
        help="Print argparse help for a specific subcommand. Repeatable.",
    )
    parser.add_argument(
        "--all-task-help",
        action="store_true",
        help="Print argparse help for every discovered subcommand.",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only print a source-derived task/flag summary; do not execute argparse help.",
    )
    parser.add_argument(
        "--show-location",
        action="store_true",
        help="Print the resolved installed package and script paths.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Seconds allowed for each help subprocess (default: 10).",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    package_dir, script = locate_package()
    tasks = extract_tasks(script)

    if args.show_location:
        print(f"package_dir={package_dir}")
        print(f"audioAnalysis_py={script}")

    task_names = [str(t["name"]) for t in tasks]
    requested_tasks = list(args.task)
    if args.all_task_help:
        requested_tasks.extend(task_names)

    status = 0
    if not args.list_only and not requested_tasks:
        print("== audioAnalysis.py top-level help ==")
        status = run_help(script, package_dir, None, args.timeout)

    if requested_tasks and not args.list_only:
        unknown = [task for task in requested_tasks if task not in task_names]
        if unknown:
            print("Unknown task name(s): " + ", ".join(unknown), file=sys.stderr)
            print("Use --list-only to see discovered task names.", file=sys.stderr)
            return 2
        for task in requested_tasks:
            print(f"\n== audioAnalysis.py {task} --help ==")
            rc = run_help(script, package_dir, task, args.timeout)
            status = status or rc

    print_task_summary(tasks)
    return int(status != 0)


if __name__ == "__main__":
    raise SystemExit(main())
