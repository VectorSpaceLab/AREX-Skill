#!/usr/bin/env python3
"""Safe Aim CLI smoke checks.

The script verifies help/version surfaces for Aim's CLI and optionally
initializes a temporary or user-provided repository with --skip-if-exists.
It never starts aim up/server listeners and never runs destructive runs/storage
commands.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


Command = Tuple[str, Sequence[str], Sequence[str]]


def _resolve_executable(explicit: Optional[str], name: str) -> str:
    if explicit:
        candidate = Path(explicit).expanduser()
        if candidate.exists():
            return str(candidate)
        raise SystemExit(f"error: explicit {name} executable does not exist: {candidate}")
    found = shutil.which(name)
    if found:
        return found
    sibling = Path(sys.executable).resolve().parent / name
    if sibling.exists():
        return str(sibling)
    option = "--aim-bin" if name == "aim" else "--watcher-bin"
    raise SystemExit(
        f"error: could not find {name!r} on PATH or beside the current Python executable; "
        f"activate the Aim environment or pass {option}"
    )


def _run(label: str, argv: Sequence[str], cwd: Path, expected: Iterable[str]) -> Tuple[bool, str]:
    proc = subprocess.run(
        list(argv),
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    missing = [token for token in expected if token not in output]
    ok = proc.returncode == 0 and not missing
    if ok:
        print(f"PASS {label}")
    else:
        print(f"FAIL {label}")
        print(f"  command: {' '.join(map(str, argv))}")
        print(f"  returncode: {proc.returncode}")
        if missing:
            print(f"  missing expected text: {missing}")
        tail = "\n".join(output.strip().splitlines()[-12:])
        if tail:
            print("  output tail:")
            for line in tail.splitlines():
                print(f"    {line}")
    return ok, output


def _prepare_repo(aim_bin: str, init_dir: Optional[Path], cwd: Path) -> Tuple[Optional[Path], bool]:
    """Return (repo_dir, cleanup_repo_dir)."""
    if init_dir is None:
        repo_dir = Path(tempfile.mkdtemp(prefix="aim-cli-smoke-"))
        cleanup = True
    else:
        repo_dir = init_dir.expanduser().resolve()
        repo_dir.mkdir(parents=True, exist_ok=True)
        cleanup = False

    proc = subprocess.run(
        [aim_bin, "init", "--repo", str(repo_dir), "--skip-if-exists"],
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    init_output = (proc.stdout or "") + (proc.stderr or "")
    ok = proc.returncode == 0 and (
        "Initialized" in init_output or "Skipped initialization" in init_output or (repo_dir / ".aim").exists()
    )
    if ok:
        print("PASS aim init --skip-if-exists")
    else:
        print("FAIL aim init --skip-if-exists")
        print(f"  command: {aim_bin} init --repo {repo_dir} --skip-if-exists")
        print(f"  returncode: {proc.returncode}")
        tail = "\n".join(init_output.strip().splitlines()[-12:])
        if tail:
            print("  output tail:")
            for line in tail.splitlines():
                print(f"    {line}")
    if not ok:
        if cleanup:
            shutil.rmtree(repo_dir, ignore_errors=True)
        raise SystemExit("error: aim init smoke failed")
    if not (repo_dir / ".aim").exists():
        if cleanup:
            shutil.rmtree(repo_dir, ignore_errors=True)
        raise SystemExit(f"error: aim init did not create .aim under {repo_dir}")
    print(f"PASS .aim exists in smoke repo: {repo_dir}")
    return repo_dir, cleanup


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run safe Aim CLI help/version/init smoke checks.")
    parser.add_argument("--aim-bin", help="Path to the aim executable. Defaults to PATH lookup.")
    parser.add_argument("--watcher-bin", help="Path to the aim-watcher executable. Defaults to PATH lookup.")
    parser.add_argument(
        "--init-dir",
        type=Path,
        help="Directory to initialize with 'aim init --skip-if-exists'. Created if missing. Defaults to a temp dir.",
    )
    parser.add_argument(
        "--no-init",
        action="store_true",
        help="Skip the init check. Nested converter help requiring a repo is also skipped.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary repo created by the script for inspection.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    aim_bin = _resolve_executable(args.aim_bin, "aim")
    watcher_bin = _resolve_executable(args.watcher_bin, "aim-watcher")

    scratch_cwd = Path(tempfile.mkdtemp(prefix="aim-cli-smoke-cwd-"))
    repo_dir: Optional[Path] = None
    cleanup_repo = False
    failures: List[str] = []

    try:
        commands: List[Command] = [
            ("aim --help", [aim_bin, "--help"], ["Commands:", "init", "up", "server", "runs", "storage", "convert"]),
            ("aim version", [aim_bin, "version"], ["Aim v"]),
            ("aim init --help", [aim_bin, "init", "--help"], ["--repo", "--skip-if-exists"]),
            ("aim up --help", [aim_bin, "up", "--help"], ["--host", "--port", "--base-path", "--read-only"]),
            ("aim server --help", [aim_bin, "server", "--help"], ["--host", "--port", "--base-path", "--ssl-certfile"]),
            ("aim runs --help", [aim_bin, "runs", "--help"], ["ls", "rm", "close", "update-metrics"]),
            ("aim storage --help", [aim_bin, "storage", "--help"], ["upgrade", "restore", "prune", "reindex"]),
            ("aim convert --help", [aim_bin, "convert", "--help"], ["tensorboard", "mlflow", "wandb"]),
            ("aim-watcher --help", [watcher_bin, "--help"], ["notifiers", "start", "--repo"]),
        ]

        for label, cmd, expected in commands:
            ok, _ = _run(label, cmd, scratch_cwd, expected)
            if not ok:
                failures.append(label)

        if not args.no_init:
            repo_dir, cleanup_repo = _prepare_repo(aim_bin, args.init_dir, scratch_cwd)
            repo_commands: List[Command] = [
                (
                    "aim convert tensorboard --help",
                    [aim_bin, "convert", "--repo", str(repo_dir), "tensorboard", "--help"],
                    ["--logdir", "--flat", "--no-cache"],
                ),
                (
                    "aim convert mlflow --help",
                    [aim_bin, "convert", "--repo", str(repo_dir), "mlflow", "--help"],
                    ["--tracking_uri", "--experiment"],
                ),
                (
                    "aim-watcher notifiers --help",
                    [watcher_bin, "--repo", str(repo_dir), "notifiers", "--help"],
                    ["add", "list", "set-log-level"],
                ),
                (
                    "aim-watcher notifier add help",
                    [watcher_bin, "--repo", str(repo_dir), "notifiers", "add", "--help"],
                    ["logger", "slack", "workplace"],
                ),
                (
                    "aim-watcher logger notifier help",
                    [watcher_bin, "--repo", str(repo_dir), "notifiers", "add", "logger", "--help"],
                    ["--message"],
                ),
            ]
            for label, cmd, expected in repo_commands:
                ok, _ = _run(label, cmd, scratch_cwd, expected)
                if not ok:
                    failures.append(label)

        if failures:
            print("\nFAILED safe Aim CLI smoke checks:")
            for failure in failures:
                print(f"- {failure}")
            return 1

        print("\nAll safe Aim CLI smoke checks passed.")
        if repo_dir and (not cleanup_repo or args.keep_temp):
            print(f"Smoke repository kept at: {repo_dir}")
        return 0
    finally:
        shutil.rmtree(scratch_cwd, ignore_errors=True)
        if repo_dir and cleanup_repo and not args.keep_temp:
            shutil.rmtree(repo_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
