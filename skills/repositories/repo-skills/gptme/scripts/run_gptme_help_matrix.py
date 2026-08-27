#!/usr/bin/env python3
"""Run safe gptme console-script help/list checks with timeouts.

This helper never starts a chat, server, browser, model call, Docker build, or
benchmark run. It only invokes help-style commands and the safe eval suite list.

Examples:
  python run_gptme_help_matrix.py
  python run_gptme_help_matrix.py --json --timeout 15
  python run_gptme_help_matrix.py --only gptme --only gptme-server
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Sequence

DEFAULT_CHECKS: dict[str, list[str]] = {
    "gptme": ["gptme", "--help"],
    "gptme-util": ["gptme-util", "--help"],
    "gptme-server": ["gptme-server", "--help"],
    "gptme-auth": ["gptme-auth", "--help"],
    "gptme-agent": ["gptme-agent", "--help"],
    "gptme-doctor": ["gptme-doctor", "--help"],
    "gptme-tui": ["gptme-tui", "--help"],
    "gptme-mcp-server": ["gptme-mcp-server", "--help"],
    "gptme-eval-list": ["gptme-eval", "--list"],
}


@dataclass
class CheckResult:
    name: str
    command: list[str]
    status: str
    returncode: int | None
    first_line: str
    stderr_first_line: str
    message: str = ""


def run_check(name: str, command: Sequence[str], timeout: float) -> CheckResult:
    executable = shutil.which(command[0])
    if executable is None:
        return CheckResult(
            name=name,
            command=list(command),
            status="missing",
            returncode=None,
            first_line="",
            stderr_first_line="",
            message=f"{command[0]} was not found on PATH",
        )
    try:
        completed = subprocess.run(
            list(command),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name=name,
            command=list(command),
            status="timeout",
            returncode=None,
            first_line="",
            stderr_first_line="",
            message=f"timed out after {timeout:g}s",
        )
    stdout_lines = [line for line in completed.stdout.splitlines() if line.strip()]
    stderr_lines = [line for line in completed.stderr.splitlines() if line.strip()]
    ok = completed.returncode == 0 and bool(stdout_lines or stderr_lines)
    return CheckResult(
        name=name,
        command=list(command),
        status="ok" if ok else "fail",
        returncode=completed.returncode,
        first_line=stdout_lines[0] if stdout_lines else "",
        stderr_first_line=stderr_lines[0] if stderr_lines else "",
        message="" if ok else "expected exit 0 with help/list output",
    )


def selected_checks(only: list[str], skip_eval_list: bool) -> dict[str, list[str]]:
    checks = dict(DEFAULT_CHECKS)
    if skip_eval_list:
        checks.pop("gptme-eval-list", None)
    if only:
        unknown = sorted(set(only).difference(checks))
        if unknown:
            raise SystemExit(f"unknown check(s): {', '.join(unknown)}")
        checks = {name: checks[name] for name in only}
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=20.0, help="Per-command timeout in seconds.")
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help=f"Run one named check; repeat as needed. Known: {', '.join(DEFAULT_CHECKS)}",
    )
    parser.add_argument(
        "--skip-eval-list",
        action="store_true",
        help="Skip `gptme-eval --list` when eval imports are not installed.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = parser.parse_args()

    checks = selected_checks(args.only, args.skip_eval_list)
    results = [run_check(name, command, args.timeout) for name, command in checks.items()]
    status = "ok" if all(result.status == "ok" for result in results) else "fail"
    if args.json:
        print(json.dumps({"status": status, "results": [asdict(r) for r in results]}, indent=2))
    else:
        for result in results:
            line = f"{result.name}: {result.status} rc={result.returncode} first={result.first_line or result.stderr_first_line!r}"
            if result.message:
                line += f" message={result.message}"
            print(line)
        print(f"overall: {status}")
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
