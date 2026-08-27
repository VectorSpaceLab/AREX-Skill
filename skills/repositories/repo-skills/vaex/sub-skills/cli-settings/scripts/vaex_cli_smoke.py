#!/usr/bin/env python3
"""Run bounded, non-destructive checks against an installed Vaex CLI.

The script never uses a repository checkout, network path, credentials, alias
writes, settings saves, conversion, server startup, benchmarks, or tests. With
--open-csv it creates one tiny temporary CSV and checks it with
``vaex open --dry-run``; the command intentionally does not pass --delete.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Sequence


DEFAULT_TIMEOUT = 20.0


def _find_cli() -> list[str] | None:
    """Return an argv prefix for the installed console or module fallback."""
    executable = shutil.which("vaex")
    if executable:
        return [executable]
    # Keep the fallback in the same interpreter that invoked this helper.
    try:
        probe = subprocess.run(
            [sys.executable, "-m", "vaex", "--help"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=DEFAULT_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return [sys.executable, "-m", "vaex"] if probe.returncode == 0 else None


def _run(prefix: Sequence[str], args: Sequence[str], timeout: float) -> dict[str, Any]:
    command = [*prefix, *args]
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command": list(args),
            "returncode": None,
            "timed_out": True,
            "stdout": (exc.stdout or "")[-4000:],
            "stderr": (exc.stderr or "")[-4000:],
        }
    except OSError as exc:
        return {
            "command": list(args),
            "returncode": None,
            "timed_out": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "command": list(args),
        "returncode": completed.returncode,
        "timed_out": False,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def _temporary_csv() -> tuple[tempfile.TemporaryDirectory[str], Path]:
    directory = tempfile.TemporaryDirectory(prefix="vaex-cli-smoke-")
    path = Path(directory.name) / "tiny.csv"
    path.write_text("x,label\n1,a\n2,b\n", encoding="utf-8")
    return directory, path


def run(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    prefix = _find_cli()
    if prefix is None:
        return (
            {
                "ok": False,
                "error": "Vaex console command and python -m vaex fallback are unavailable",
                "hint": "Install a public Vaex package in the active Python environment.",
            },
            2,
        )

    results: list[dict[str, Any]] = []
    # These commands only print help/version or effective read-only settings.
    for command in (("--help",), ("version",), ("open", "--help"), ("settings", "yaml")):
        result = _run(prefix, command, args.timeout)
        result["ok"] = result.get("returncode") == 0 and not result.get("timed_out")
        if command == ("version",) and not result["ok"]:
            fallback = _run(
                [sys.executable],
                ["-c", "import vaex; print(getattr(vaex, '__version__', 'unknown'))"],
                args.timeout,
            )
            fallback["ok"] = fallback.get("returncode") == 0 and not fallback.get("timed_out")
            result["fallback"] = fallback
            result["ok"] = fallback["ok"]
        results.append(result)

    temporary: tempfile.TemporaryDirectory[str] | None = None
    if args.open_csv:
        temporary, csv_path = _temporary_csv()
        try:
            result = _run(
                prefix,
                ("open", "--dry-run", "--verbose", os.fspath(csv_path)),
                args.timeout,
            )
            result["ok"] = result.get("returncode") == 0 and not result.get("timed_out")
            result["safety"] = "--delete was not supplied"
            results.append(result)
        finally:
            # Temporary fixture cleanup is limited to this script's own directory.
            temporary.cleanup()

    failed = [item for item in results if not item.get("ok")]
    summary: dict[str, Any] = {
        "ok": not failed,
        "cli": " ".join(prefix),
        "checks": results,
        "open_csv_requested": bool(args.open_csv),
        "mutations": [],
        "network": False,
    }
    return summary, 0 if not failed else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check an installed Vaex CLI with safe help/version/settings commands."
    )
    parser.add_argument(
        "--open-csv",
        action="store_true",
        help="create a tiny temporary CSV and run vaex open --dry-run --verbose on it",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="per-command timeout in seconds (default: %(default)s)",
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--pretty", action="store_true", help="indent JSON output")
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    summary, status = run(args)
    if args.json or args.pretty:
        print(json.dumps(summary, indent=2 if args.pretty else None, sort_keys=True))
    else:
        print("Vaex CLI smoke: %s" % ("passed" if summary["ok"] else "failed"))
        for check in summary.get("checks", []):
            print("  %s -> %s" % (" ".join(check["command"]), check.get("returncode")))
        if not summary["ok"]:
            print(json.dumps(summary, indent=2, sort_keys=True), file=sys.stderr)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
