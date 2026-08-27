#!/usr/bin/env python3
"""Tiny no-download smoke check for the NLTK tokenize CLI.

The script invokes the installed ``nltk`` console script with a one-line stdin
fixture. It does not call nltk.download(), require Punkt data, or depend on the
original source checkout. By default it uses --preserve-line so sentence
 tokenization is skipped.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _console_command() -> str:
    """Find the installed console script without relying on shell activation."""
    found = shutil.which("nltk")
    if found:
        return found
    sibling = Path(sys.executable).with_name("nltk")
    if sibling.exists():
        return str(sibling)
    sibling_exe = sibling.with_suffix(".exe")
    if sibling_exe.exists():
        return str(sibling_exe)
    raise FileNotFoundError(
        "Could not find the installed 'nltk' console script. Install NLTK and "
        "ensure its environment scripts directory is available."
    )


def run_smoke(text: str = "Hello, world!\n", delimiter: str = "|") -> dict[str, Any]:
    try:
        import nltk
    except Exception as exc:  # pragma: no cover - runtime environment dependent
        raise RuntimeError("Could not import NLTK in the active Python environment") from exc

    command = _console_command()
    help_result = subprocess.run(
        [command, "tokenize", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    if help_result.returncode != 0:
        raise RuntimeError(f"nltk tokenize --help failed: {help_result.stderr or help_result.stdout}")
    help_output = help_result.stdout + help_result.stderr
    required_help = ["--language", "--preserve-line", "--processes", "--encoding", "--delimiter"]
    missing = [flag for flag in required_help if flag not in help_output]
    if missing:
        raise AssertionError(f"nltk tokenize --help missing expected flags: {missing}")
    if "-p, --preserve-line" not in help_output:
        raise AssertionError("Expected -p to be the short flag for --preserve-line")

    result = subprocess.run(
        [command, "tokenize", "--preserve-line", "--delimiter", delimiter],
        input=text,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"nltk tokenize smoke failed: {result.stderr or result.stdout}")

    # Progress is written to stderr; stdout is the semantic tokenized stream.
    observed = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    expected = f"Hello{delimiter},{delimiter}world{delimiter}!"
    if observed != expected:
        raise AssertionError(
            f"expected CLI tokens {expected!r}, got {observed!r}; "
            f"stderr={result.stderr!r}"
        )

    return {
        "status": "ok",
        "python": platform.python_version(),
        "nltk_version": getattr(nltk, "__version__", "unknown"),
        "console_command": command,
        "help_flags_present": required_help,
        "preserve_line_short_flag": "-p",
        "input": text,
        "delimiter": delimiter,
        "observed": observed,
        "downloads_invoked": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a deterministic no-download smoke check for the NLTK tokenize CLI."
    )
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    parser.add_argument("--text", default="Hello, world!\n", help="input text passed to the CLI fixture")
    parser.add_argument("--delimiter", default="|", help="delimiter passed to nltk tokenize")
    args = parser.parse_args(argv)

    try:
        summary = run_smoke(args.text, args.delimiter)
    except Exception as exc:
        print(f"tokenize_cli_smoke: FAIL: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print("tokenize_cli_smoke: OK")
        for key in sorted(summary):
            print(f"  {key}: {summary[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
