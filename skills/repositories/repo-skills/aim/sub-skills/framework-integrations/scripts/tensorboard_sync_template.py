#!/usr/bin/env python3
"""Build or run safe Aim TensorBoard conversion/sync templates.

The script performs no training. It prints a conversion command by default and
runs it only when --execute is supplied. Use --sync-template to print a Python
live-sync skeleton instead of converting offline logs.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import shlex
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


EVENT_MARKERS = ("events.out.tfevents", ".tfevents")


def has_module(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def resolve_existing_dir(path_text: str, label: str) -> Path:
    path = Path(path_text).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"{label} does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"{label} is not a directory: {path}")
    if not os.access(path, os.R_OK):
        raise ValueError(f"{label} is not readable: {path}")
    return path


def find_event_files(logdir: Path, limit: int = 10) -> List[Path]:
    found: List[Path] = []
    for root, _dirs, files in os.walk(logdir):
        for filename in files:
            if any(marker in filename for marker in EVENT_MARKERS):
                found.append(Path(root) / filename)
                if len(found) >= limit:
                    return found
    return found


def build_convert_command(logdir: Path, repo: Optional[Path], flat: bool, no_cache: bool) -> List[str]:
    cmd = ["aim", "convert"]
    if repo is not None:
        cmd.extend(["--repo", str(repo)])
    cmd.extend(["tensorboard", "--logdir", str(logdir)])
    if flat:
        cmd.append("--flat")
    if no_cache:
        cmd.append("--no-cache")
    return cmd


def print_dependency_check() -> None:
    checks = {
        "aim": has_module("aim"),
        "tensorflow": has_module("tensorflow"),
        "tensorboard": has_module("tensorboard"),
    }
    for name, ok in checks.items():
        print(f"{name}: {'present' if ok else 'missing'}")
    if not checks["tensorflow"]:
        print("warning: Aim's offline TensorBoard converter reports failure when tensorflow cannot be imported.")
    if not checks["tensorboard"]:
        print("warning: TensorBoard event-processing utilities may be unavailable.")


def print_sync_template(logdir: Optional[Path], repo: Optional[Path], experiment: str) -> None:
    logdir_text = str(logdir) if logdir else "path/to/tensorboard-logdir"
    repo_text = str(repo) if repo else "path/to/aim-repo"
    template = f'''
from aim.ext.tensorboard_tracker import Run as AimTensorBoardRun

run = AimTensorBoardRun(
    sync_tensorboard_log_dir={logdir_text!r},
    repo={repo_text!r},
    experiment={experiment!r},
)
try:
    # Keep this process alive while an existing TensorBoard writer is producing events.
    # Do not add training here unless the user explicitly wants live sync during training.
    pass
finally:
    run.close()
'''
    print(textwrap.dedent(template).strip())


def shell_join(cmd: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate TensorBoard logdir inputs and print or execute Aim TensorBoard conversion commands.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--logdir", help="Existing TensorBoard log directory to convert or sync.")
    parser.add_argument("--repo", help="Existing target Aim repository directory. Required for --execute to avoid cwd ambiguity.")
    parser.add_argument("--flat", action="store_true", help="Pass --flat to aim convert tensorboard.")
    parser.add_argument("--no-cache", action="store_true", help="Pass --no-cache to reprocess logs instead of using converter cache.")
    parser.add_argument("--allow-empty", action="store_true", help="Allow conversion command generation/execution even if no event files are found.")
    parser.add_argument("--check-deps", action="store_true", help="Check lightweight module presence for aim/tensorflow/tensorboard.")
    parser.add_argument("--sync-template", action="store_true", help="Print a Python live-sync template instead of an offline conversion command.")
    parser.add_argument("--experiment", default="tensorboard_sync", help="Experiment name used in the live-sync template.")
    parser.add_argument("--execute", action="store_true", help="Actually run the offline conversion command. Never runs training.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if len(sys.argv if argv is None else argv) == 1:
        parser.print_help()
        return 0

    if args.check_deps:
        print_dependency_check()

    logdir: Optional[Path] = None
    repo: Optional[Path] = None

    try:
        if args.logdir:
            logdir = resolve_existing_dir(args.logdir, "logdir")
            event_files = find_event_files(logdir)
            if event_files:
                print(f"event files found: {len(event_files)} shown/sample limit")
                for event_file in event_files[:5]:
                    print(f"  {event_file}")
            else:
                message = f"no TensorBoard event files found under {logdir}"
                if args.allow_empty:
                    print(f"warning: {message}")
                else:
                    raise ValueError(message + " (use --allow-empty to override)")
        elif args.sync_template or args.execute:
            raise ValueError("--logdir is required for --sync-template and --execute")

        if args.repo:
            repo = resolve_existing_dir(args.repo, "repo")
        elif args.execute:
            raise ValueError("--repo is required with --execute so conversion does not depend on the current directory")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.sync_template:
        print_sync_template(logdir, repo, args.experiment)
        return 0

    if logdir is None:
        if not args.check_deps:
            parser.print_help()
        return 0

    cmd = build_convert_command(logdir, repo, args.flat, args.no_cache)
    print("offline conversion command:")
    print(shell_join(cmd))

    if not args.execute:
        print("not executed; add --execute to run conversion after reviewing the command")
        return 0

    aim_exe = shutil.which("aim")
    if not aim_exe:
        print("error: 'aim' executable was not found on PATH", file=sys.stderr)
        return 127
    cmd[0] = aim_exe
    completed = subprocess.run(cmd, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
