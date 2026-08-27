#!/usr/bin/env python3
"""Safely validate PARL xparl CLI help output.

The default behavior is non-mutating: it runs only help commands such as
`xparl --help` and `xparl start --help`. It never runs `xparl start`,
`xparl connect`, `xparl status`, or `xparl stop` without `--help`.

Examples:
  python scripts/check_xparl_cli.py
  python scripts/check_xparl_cli.py --json
  python scripts/check_xparl_cli.py --mode module
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

EXPECTED_TOKENS: Dict[str, List[str]] = {
    "root": ["start", "connect", "stop", "status"],
    "start": [
        "--port",
        "--debug",
        "--cpu_num",
        "--gpu_cluster",
        "--gpu",
        "--monitor_port",
        "--log_server_port_range",
    ],
    "connect": ["--address", "--cpu_num", "--gpu", "--log_server_port_range"],
    "status": [],
    "stop": [],
}

HELP_TARGETS: Tuple[Tuple[str, ...], ...] = (
    tuple(),
    ("start",),
    ("connect",),
    ("status",),
    ("stop",),
)


@dataclass
class CheckResult:
    target: str
    command_kind: str
    ok: bool
    returncode: Optional[int]
    missing_tokens: List[str]
    message: str


def _display_target(parts: Sequence[str]) -> str:
    return "root" if not parts else " ".join(parts)


def _expected_key(parts: Sequence[str]) -> str:
    return "root" if not parts else parts[0]


def _build_command(mode: str, xparl_command: str, parts: Sequence[str]) -> Tuple[Optional[List[str]], str, str]:
    """Return (command, command_kind, error_message)."""
    suffix = list(parts) + ["--help"]
    if mode in {"auto", "xparl"}:
        binary = shutil.which(xparl_command)
        if binary:
            return [binary] + suffix, "xparl", ""
        if mode == "xparl":
            return None, "xparl", f"Could not find {xparl_command!r} on PATH."

    if mode in {"auto", "module"}:
        return [sys.executable, "-m", "parl.remote.scripts"] + suffix, "module", ""

    return None, mode, f"Unsupported mode: {mode}"


def _run_help(command: Sequence[str], timeout: float) -> Tuple[int, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    proc = subprocess.run(
        list(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        env=env,
        check=False,
    )
    return proc.returncode, proc.stdout or ""


def _redact_paths(text: str) -> str:
    """Avoid echoing machine-specific paths in diagnostic summaries."""
    text = re.sub(r'File "[^"]+"', 'File "<path>"', text)
    text = re.sub(r"(?<![A-Za-z0-9_.-])/(?:[^\s:'\"]+/)*[^\s:'\"]+", "<path>", text)
    text = re.sub(r"(?<![A-Za-z0-9_.-])~/(?:[^\s:'\"]+/)*[^\s:'\"]+", "<path>", text)
    return text


def _check_target(mode: str, xparl_command: str, parts: Sequence[str], timeout: float) -> CheckResult:
    target = _display_target(parts)
    command, command_kind, error = _build_command(mode, xparl_command, parts)
    if command is None:
        return CheckResult(
            target=target,
            command_kind=command_kind,
            ok=False,
            returncode=None,
            missing_tokens=EXPECTED_TOKENS.get(_expected_key(parts), []),
            message=error,
        )

    try:
        returncode, output = _run_help(command, timeout)
    except subprocess.TimeoutExpired:
        return CheckResult(
            target=target,
            command_kind=command_kind,
            ok=False,
            returncode=None,
            missing_tokens=EXPECTED_TOKENS.get(_expected_key(parts), []),
            message=f"Timed out while reading help for {target}.",
        )
    except OSError as exc:
        return CheckResult(
            target=target,
            command_kind=command_kind,
            ok=False,
            returncode=None,
            missing_tokens=EXPECTED_TOKENS.get(_expected_key(parts), []),
            message=f"Could not execute help command for {target}: {exc}",
        )

    expected = EXPECTED_TOKENS.get(_expected_key(parts), [])
    missing = [token for token in expected if token not in output]
    ok = returncode == 0 and not missing
    if ok:
        message = f"Help output for {target} contains expected tokens."
    else:
        snippets = []
        if returncode != 0:
            snippets.append(f"return code {returncode}")
        if missing:
            snippets.append("missing: " + ", ".join(missing))
        tail = "\n".join(output.strip().splitlines()[-8:])
        if tail:
            snippets.append("last output lines (paths redacted):\n" + _redact_paths(tail))
        message = "; ".join(snippets) if snippets else f"Help check failed for {target}."

    return CheckResult(
        target=target,
        command_kind=command_kind,
        ok=ok,
        returncode=returncode,
        missing_tokens=missing,
        message=message,
    )


def run_checks(mode: str, xparl_command: str, timeout: float, targets: Iterable[Sequence[str]]) -> List[CheckResult]:
    return [_check_target(mode, xparl_command, parts, timeout) for parts in targets]


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run safe help-only checks for the PARL xparl CLI. No cluster processes are started or stopped.",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "xparl", "module"),
        default="auto",
        help="How to invoke help: installed xparl command, python module fallback, or auto.",
    )
    parser.add_argument(
        "--xparl-command",
        default="xparl",
        help="Console command name to look up when mode is auto or xparl.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Seconds allowed for each help command.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human-readable summary.",
    )
    parser.add_argument(
        "--root-only",
        action="store_true",
        help="Check only xparl --help, not subcommand help pages.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    targets = (tuple(),) if args.root_only else HELP_TARGETS
    results = run_checks(args.mode, args.xparl_command, args.timeout, targets)
    overall_ok = all(result.ok for result in results)

    if args.json:
        print(json.dumps({"ok": overall_ok, "results": [asdict(r) for r in results]}, indent=2, sort_keys=True))
    else:
        print("xparl help-only check")
        print("mode:", args.mode)
        print("mutating commands: not executed")
        for result in results:
            status = "OK" if result.ok else "FAIL"
            print(f"[{status}] {result.target} via {result.command_kind}: {result.message}")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
