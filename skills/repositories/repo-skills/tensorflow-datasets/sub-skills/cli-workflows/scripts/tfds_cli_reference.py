#!/usr/bin/env python3
"""Check the installed TensorFlow Datasets CLI help and version.

This script is a lightweight runtime probe. It does not import TensorFlow
Datasets directly; it executes the `tfds` entry point (or a user-supplied
binary) with `--version` and `--help` arguments and verifies that key commands
and flags are present.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Iterable, Sequence

COMMAND_FLAG_EXPECTATIONS = {
    "top": ["build", "new", "convert_format", "build_croissant", "--dry_run"],
    "build": ["--data_dir", "--max_examples_per_split", "--config_idx", "--imports", "--file_format", "--num-processes"],
    "new": ["dataset_name", "--data_format", "--dir"],
    "convert_format": ["--dataset_version_dir", "--out_file_format", "--out_dir", "--overwrite", "--num_workers"],
    "build_croissant": ["--jsonld", "--data_dir", "--file_format", "--record_sets", "--mapping"],
}


@dataclass
class CommandCheck:
    name: str
    argv: list[str]
    exit_code: int | None
    ok: bool
    missing_tokens: list[str]
    stdout_excerpt: str
    stderr_excerpt: str
    error: str | None = None


def _excerpt(text: str, max_chars: int = 1600) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...<truncated>"


def _run(argv: Sequence[str], timeout: float) -> tuple[int | None, str, str, str | None]:
    try:
        completed = subprocess.run(
            list(argv),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        return completed.returncode, completed.stdout, completed.stderr, None
    except FileNotFoundError as exc:
        return None, "", "", str(exc)
    except subprocess.TimeoutExpired as exc:
        return None, exc.stdout or "", exc.stderr or "", f"timed out after {timeout} seconds"


def _check(tfds_bin: str, name: str, args: Sequence[str], expected: Sequence[str], timeout: float) -> CommandCheck:
    argv = [tfds_bin, *args]
    code, stdout, stderr, error = _run(argv, timeout=timeout)
    combined = stdout + "\n" + stderr
    missing = [token for token in expected if token not in combined]
    ok = (code == 0) and not missing and error is None
    return CommandCheck(
        name=name,
        argv=argv,
        exit_code=code,
        ok=ok,
        missing_tokens=missing,
        stdout_excerpt=_excerpt(stdout),
        stderr_excerpt=_excerpt(stderr),
        error=error,
    )


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check installed `tfds` CLI help and version.")
    parser.add_argument("--tfds-bin", default="tfds", help="Executable to run; defaults to `tfds` on PATH.")
    parser.add_argument(
        "--commands",
        default="top,build,new,convert_format,build_croissant",
        help="Comma-separated help pages to check. Use `top` for `tfds --help`.",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout per command in seconds.")
    parser.add_argument("--show-help", action="store_true", help="Print help excerpts in text mode.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def run_checks(tfds_bin: str, commands: Iterable[str], timeout: float) -> dict[str, object]:
    resolved = shutil.which(tfds_bin) if not any(sep in tfds_bin for sep in ("/", "\\")) else tfds_bin
    checks: list[CommandCheck] = []

    version_code, version_stdout, version_stderr, version_error = _run([tfds_bin, "--version"], timeout=timeout)
    version_ok = version_code == 0 and version_error is None and "TensorFlow Datasets" in (version_stdout + version_stderr)

    command_args = {
        "top": ["--help"],
        "build": ["build", "--help"],
        "new": ["new", "--help"],
        "convert_format": ["convert_format", "--help"],
        "build_croissant": ["build_croissant", "--help"],
    }
    for name in commands:
        name = name.strip()
        if not name:
            continue
        if name not in command_args:
            raise ValueError(f"Unknown command check {name!r}; expected one of {sorted(command_args)}")
        checks.append(
            _check(
                tfds_bin=tfds_bin,
                name=name,
                args=command_args[name],
                expected=COMMAND_FLAG_EXPECTATIONS[name],
                timeout=timeout,
            )
        )

    overall_ok = bool(resolved) and version_ok and all(check.ok for check in checks)
    return {
        "ok": overall_ok,
        "tfds_bin_found": bool(resolved),
        "version": {
            "ok": version_ok,
            "exit_code": version_code,
            "stdout_excerpt": _excerpt(version_stdout),
            "stderr_excerpt": _excerpt(version_stderr),
            "error": version_error,
        },
        "checks": [asdict(check) for check in checks],
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        report = run_checks(
            tfds_bin=args.tfds_bin,
            commands=args.commands.split(","),
            timeout=args.timeout,
        )
    except Exception as exc:
        parser.error(str(exc))
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        status = "OK" if report["ok"] else "FAIL"
        print(f"TFDS CLI reference check: {status}")
        print(f"tfds binary found: {report['tfds_bin_found']}")
        version = report["version"]
        print(f"version check: {'OK' if version['ok'] else 'FAIL'}")
        if version.get("stdout_excerpt"):
            print(version["stdout_excerpt"])
        for check in report["checks"]:
            print(f"{check['name']}: {'OK' if check['ok'] else 'FAIL'}")
            if check["missing_tokens"]:
                print(f"  missing: {', '.join(check['missing_tokens'])}")
            if check.get("error"):
                print(f"  error: {check['error']}")
            if args.show_help and check.get("stdout_excerpt"):
                print(check["stdout_excerpt"])
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
