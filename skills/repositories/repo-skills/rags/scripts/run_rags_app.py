#!/usr/bin/env python3
"""Prepare or execute the RAGs Streamlit app launch command.

By default this wrapper performs validation and prints the command it would run.
Pass --execute only when the user intends to start the long-running Streamlit
server. The wrapper accepts a checkout path explicitly and does not assume it is
run from the repository root.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

HOME_ENTRYPOINT = "1_🏠_Home.py"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dry-run or execute RAGs Streamlit launch.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to a RAGs checkout. Default: current working directory.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually start Streamlit. Without this flag the command is only printed.",
    )
    parser.add_argument(
        "--check-secrets",
        action="store_true",
        help="Check whether a Streamlit secrets file appears to contain openai_key.",
    )
    parser.add_argument(
        "--json-indent",
        type=int,
        default=2,
        help="Indentation for dry-run JSON output. Use 0 for compact output.",
    )
    parser.add_argument(
        "streamlit_args",
        nargs=argparse.REMAINDER,
        help="Extra arguments after -- are forwarded to streamlit run.",
    )
    return parser


def _find_home(repo_root: Path) -> Path | None:
    exact = repo_root / HOME_ENTRYPOINT
    if exact.exists():
        return exact
    matches = sorted(repo_root.glob("1_*Home.py"))
    return matches[0] if matches else None


def _secret_candidates(repo_root: Path) -> list[Path]:
    return [repo_root / ".streamlit" / "secrets.toml", Path.home() / ".streamlit" / "secrets.toml"]


def _has_openai_key(path: Path) -> bool:
    try:
        text = path.read_text()
    except OSError:
        return False
    return "openai_key" in text


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    home = _find_home(repo_root)
    extra = list(args.streamlit_args)
    if extra and extra[0] == "--":
        extra = extra[1:]

    report = {
        "repo_root": str(repo_root),
        "home_entrypoint_found": home is not None,
        "home_entrypoint": None if home is None else str(home),
        "execute": args.execute,
    }

    if home is None:
        report["status"] = "failed"
        report["error"] = "could not find the RAGs Home page entrypoint"
        print(json.dumps(report, indent=None if args.json_indent == 0 else args.json_indent, sort_keys=True))
        return 1

    if args.check_secrets:
        candidates = _secret_candidates(repo_root)
        report["secret_files_checked"] = [str(path) for path in candidates]
        report["openai_key_present"] = any(_has_openai_key(path) for path in candidates)

    cmd = [sys.executable, "-m", "streamlit", "run", str(home), *extra]
    report["command"] = cmd

    if not args.execute:
        report["status"] = "dry-run"
        print(json.dumps(report, indent=None if args.json_indent == 0 else args.json_indent, sort_keys=True))
        return 0

    return subprocess.call(cmd, cwd=str(repo_root))


if __name__ == "__main__":
    raise SystemExit(main())
