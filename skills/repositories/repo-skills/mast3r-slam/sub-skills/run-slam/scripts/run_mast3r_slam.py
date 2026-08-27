#!/usr/bin/env python3
"""Build or execute a MASt3R-SLAM main.py command safely.

Default is dry-run: the script prints the command and does not run SLAM. Add
--execute only after confirming CUDA, checkpoints, input data, and runtime cost.
"""
from __future__ import annotations

import argparse
import pathlib
import shlex
import subprocess

LIVE_TOKENS = {"realsense", "webcam"}


def path_arg(value: str | None, repo_root: pathlib.Path) -> str | None:
    if not value:
        return None
    if value in LIVE_TOKENS:
        return value
    path = pathlib.Path(value)
    if path.is_absolute():
        return str(path)
    if path.exists():
        return str(path.resolve())
    if (repo_root / path).exists():
        return str(path)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path.cwd(), help="Checkout containing main.py; defaults to current directory.")
    parser.add_argument("--main", type=pathlib.Path, help="Explicit path to main.py if it is not under --repo-root.")
    parser.add_argument("--python", default="python", help="Python executable used to run main.py. Defaults to shell 'python'.")
    parser.add_argument("--dataset", required=True, help="Dataset/video/folder/live token passed to --dataset.")
    parser.add_argument("--config", required=True, help="YAML config path passed to --config.")
    parser.add_argument("--calib", help="Optional calibration YAML passed to --calib.")
    parser.add_argument("--save-as", default="default", help="Value passed to --save-as.")
    parser.add_argument("--no-viz", action="store_true", help="Pass --no-viz to the launcher.")
    parser.add_argument("--dry-run", action="store_true", help="Print command only. This is the default unless --execute is set.")
    parser.add_argument("--execute", action="store_true", help="Actually execute the command from --repo-root.")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    main_py = args.main.resolve() if args.main else repo_root / "main.py"
    if not main_py.exists():
        print(f"main.py not found: {main_py}", file=sys.stderr)
        print("Pass --repo-root <MASt3R-SLAM-checkout> or --main <path/to/main.py>.", file=sys.stderr)
        return 1

    cmd = [args.python, str(main_py), "--dataset", path_arg(args.dataset, repo_root), "--config", path_arg(args.config, repo_root)]
    if args.save_as != "default":
        cmd.extend(["--save-as", args.save_as])
    if args.no_viz:
        cmd.append("--no-viz")
    calib = path_arg(args.calib, repo_root)
    if calib:
        cmd.extend(["--calib", calib])

    print(shlex.join(cmd))
    if not args.execute:
        return 0
    return subprocess.run(cmd, cwd=repo_root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
