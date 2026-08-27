#!/usr/bin/env python3
"""Safely discover pymatgen CLI help without mutating config or data."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_COMMANDS = (
    "pmg",
    "pmg:config",
    "pmg:analyze",
    "pmg:query",
    "pmg:plot",
    "pmg:structure",
    "pmg:view",
    "pmg:diff",
    "pmg:potcar",
    "get_environment",
    "feff_plot_cross_section",
    "feff_plot_dos",
)


@dataclass(frozen=True)
class HelpTarget:
    label: str
    argv: tuple[str, ...]


def parse_target(spec: str) -> HelpTarget:
    """Parse `command` or `pmg:subcommand` into a help-only argv."""
    if ":" not in spec:
        return HelpTarget(spec, (spec, "--help"))

    command, subcommand = spec.split(":", 1)
    if not command or not subcommand:
        raise ValueError(f"invalid command spec {spec!r}; expected command or command:subcommand")
    return HelpTarget(spec, (command, subcommand, "--help"))


def find_executable(command: str) -> str | None:
    path = shutil.which(command)
    if path:
        return path
    script_dir = Path(sys.executable).resolve().parent
    candidate = script_dir / command
    if candidate.exists():
        return str(candidate)
    windows_candidate = script_dir / f"{command}.exe"
    if windows_candidate.exists():
        return str(windows_candidate)
    return None


def summarize(text: str, max_lines: int) -> str:
    """Return a bounded help summary to avoid flooding logs."""
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    omitted = len(lines) - max_lines
    return "\n".join([*lines[:max_lines], f"... ({omitted} more non-empty help lines omitted)"])


def run_help(target: HelpTarget, timeout: float, max_lines: int) -> dict[str, object]:
    """Run a single help command if its executable is discoverable."""
    executable = find_executable(target.argv[0])
    if executable is None:
        return {"label": target.label, "ok": False, "status": "missing", "summary": f"missing executable: {target.argv[0]}"}

    argv = (executable, *target.argv[1:])
    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"label": target.label, "ok": False, "status": "timeout", "summary": f"timeout after {timeout:g}s"}
    except OSError as exc:
        return {
            "label": target.label,
            "ok": False,
            "status": "failed",
            "summary": f"failed to execute: {type(exc).__name__}: {exc}",
        }

    output = completed.stdout or completed.stderr
    return {
        "label": target.label,
        "ok": completed.returncode in {0, 2},
        "status": f"exit {completed.returncode}",
        "returncode": completed.returncode,
        "summary": summarize(output, max_lines),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run --help for selected pymatgen console scripts and pmg subcommands. "
            "This probe never calls non-help commands, mutates .pmgrc.yaml, opens plots, "
            "reads credentials, scans user directories, or touches POTCAR data."
        )
    )
    parser.add_argument(
        "--commands",
        nargs="+",
        default=list(DEFAULT_COMMANDS),
        help="Commands to probe. Use pmg:subcommand for pmg subcommands.",
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="Seconds to wait for each help command.")
    parser.add_argument("--max-lines", type=int, default=24, help="Maximum non-empty help lines to print per command.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args(argv)

    results: list[dict[str, object]] = []
    for spec in args.commands:
        try:
            target = parse_target(spec)
        except ValueError as exc:
            results.append({"label": spec, "ok": False, "status": "invalid", "summary": str(exc)})
            continue
        results.append(run_help(target, args.timeout, args.max_lines))

    if args.json:
        print(json.dumps({"mutating_commands_run": False, "results": results}, indent=2, sort_keys=True))
    else:
        for result in results:
            print(f"## {result['label']} ({result['status']})")
            print(result["summary"] or "no help output captured")
            print()

    return 1 if any(not result["ok"] for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
