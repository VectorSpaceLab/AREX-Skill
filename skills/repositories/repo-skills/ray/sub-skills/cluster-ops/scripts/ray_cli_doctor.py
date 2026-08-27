#!/usr/bin/env python3
"""Safe Ray CLI availability and help checker.

This script never starts, stops, submits to, or connects to a Ray cluster. It only
checks whether the local Python environment can import Ray and whether selected
`ray ... --help` commands can be invoked.
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_COMMANDS: tuple[str, ...] = (
    "root",
    "start",
    "status",
    "job",
    "list",
    "summary",
    "logs",
)

COMMAND_ARGS: dict[str, tuple[str, ...]] = {
    "root": ("--help",),
    "start": ("start", "--help"),
    "stop": ("stop", "--help"),
    "status": ("status", "--help"),
    "job": ("job", "--help"),
    "job-submit": ("job", "submit", "--help"),
    "job-status": ("job", "status", "--help"),
    "job-logs": ("job", "logs", "--help"),
    "list": ("list", "--help"),
    "get": ("get", "--help"),
    "summary": ("summary", "--help"),
    "logs": ("logs", "--help"),
    "dashboard": ("dashboard", "--help"),
    "memory": ("memory", "--help"),
    "timeline": ("timeline", "--help"),
    "symmetric-run": ("symmetric-run", "--help"),
    "serve": ("serve", "--help"),
}


@dataclass(frozen=True)
class HelpResult:
    label: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


def _execute_help(args: tuple[str, ...], label: str, timeout: float) -> HelpResult:
    try:
        completed = subprocess.run(
            args,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return HelpResult(
            label=label,
            command=args,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as exc:
        return HelpResult(
            label=label,
            command=args,
            returncode=124,
            stdout=exc.stdout or "",
            stderr=f"Timed out after {timeout:g} seconds.",
        )
    except OSError as exc:
        return HelpResult(
            label=label,
            command=args,
            returncode=127,
            stdout="",
            stderr=str(exc),
        )


def _run_help(ray_executable: str | None, label: str, timeout: float) -> HelpResult:
    command_args = COMMAND_ARGS[label]
    if ray_executable:
        result = _execute_help((ray_executable, *command_args), label, timeout)
        if result.returncode != 127:
            return result
    return _execute_help((sys.executable, "-m", "ray.scripts.scripts", *command_args), label, timeout)


def _first_lines(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    return "\n".join(lines[:max_lines])


def _print_result(result: HelpResult, verbose: bool, max_lines: int) -> None:
    command_text = " ".join(result.command)
    status = "ok" if result.returncode == 0 else f"failed rc={result.returncode}"
    print(f"[{status}] {result.label}: {command_text}")
    if verbose or result.returncode != 0:
        output = result.stdout if result.stdout.strip() else result.stderr
        if output.strip():
            print(_first_lines(output.rstrip(), max_lines))
    elif result.stdout.strip():
        first = result.stdout.strip().splitlines()[0]
        print(f"  {first}")


def _resolve_commands(selected: Sequence[str]) -> list[str]:
    if not selected:
        return list(DEFAULT_COMMANDS)
    labels: list[str] = []
    for item in selected:
        if item == "all":
            for label in COMMAND_ARGS:
                if label not in labels:
                    labels.append(label)
        elif item in COMMAND_ARGS:
            if item not in labels:
                labels.append(item)
        else:
            choices = ", ".join(sorted(COMMAND_ARGS))
            raise SystemExit(f"Unknown command label {item!r}. Choose one of: {choices}, all")
    return labels


def _iter_import_checks() -> Iterable[tuple[str, str]]:
    yield "ray", "required for any Ray CLI use"
    yield "ray.dashboard", "needed for Jobs, dashboard, and State API features in full installs"
    yield "ray.job_submission", "needed for Jobs SDK/CLI"
    yield "ray.util.state", "needed for state/list/get/summary/log APIs"


def _module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _default_ray_executable() -> str | None:
    path_ray = shutil.which("ray")
    if path_ray:
        return path_ray
    sibling = Path(sys.executable).resolve().parent / "ray"
    if sibling.exists():
        return str(sibling)
    return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check local Ray CLI import/help availability without starting, stopping, "
            "submitting to, or connecting to a cluster."
        )
    )
    parser.add_argument(
        "--command",
        action="append",
        default=[],
        help=(
            "Help command label to check. Repeatable. Use 'all' for every known "
            "label. Defaults to root/start/status/job/list/summary/logs."
        ),
    )
    parser.add_argument(
        "--ray-bin",
        default=None,
        help="Path to the ray executable. Defaults to PATH, then the active Python environment's bin directory.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Seconds to wait for each help command. Default: 10.",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=12,
        help="Maximum help/error lines to print per command in verbose or failure mode.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the first help lines for successful commands too.",
    )
    args = parser.parse_args(argv)

    print(
        "Python version: "
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    for module_name, purpose in _iter_import_checks():
        found = _module_available(module_name)
        status = "ok" if found else "missing"
        print(f"[{status}] import {module_name} - {purpose}")

    ray_executable = args.ray_bin or _default_ray_executable()
    if ray_executable:
        print("Ray executable: found")
    else:
        print("Ray executable: not found; falling back to python -m ray.scripts.scripts")

    labels = _resolve_commands(args.command)
    failures = 0
    for label in labels:
        result = _run_help(ray_executable, label, args.timeout)
        _print_result(result, args.verbose, args.max_lines)
        if result.returncode != 0:
            failures += 1

    if failures:
        print(f"Completed with {failures} failed help check(s). No cluster was mutated.")
        return 1
    print("All selected help checks passed. No cluster was mutated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
