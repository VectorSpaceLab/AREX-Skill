#!/usr/bin/env python3
"""Preflight a local checkout and launch the speech-to-text server."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        "--root",
        dest="repo_root",
        default=str(Path.cwd()),
        help="Project root to launch from (default: current directory)",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable to use for probes and start.py (default: current interpreter)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run preflight and print the launch command without starting the server",
    )
    parser.add_argument(
        "--skip-runtime-check",
        action="store_true",
        help="Skip dependency and ffmpeg/ffprobe preflight",
    )
    parser.add_argument(
        "--skip-cuda-check",
        action="store_true",
        help="Skip CUDA preflight even when set.ini selects devtype=cuda",
    )
    return parser.parse_args()


def read_set_ini(root: Path) -> dict[str, str]:
    config: dict[str, str] = {}
    ini_path = root / "set.ini"
    if not ini_path.exists():
        return config
    for raw_line in ini_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        config[key.strip().lower()] = value.strip().lower()
    return config


def prepend_runtime_paths(root: Path) -> None:
    path_parts = [str(root)]
    ffmpeg_dir = root / "ffmpeg"
    if ffmpeg_dir.exists():
        path_parts.append(str(ffmpeg_dir))
    existing = os.environ.get("PATH", "")
    if existing:
        path_parts.append(existing)
    os.environ["PATH"] = os.pathsep.join(path_parts)


def run_helper(python_exe: str, helper: Path, *args: str, cwd: Path) -> int:
    cmd = [python_exe, "-u", str(helper), *args]
    print("[launch] " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=cwd, check=False).returncode


def main() -> int:
    args = parse_args()
    root = Path(args.repo_root).expanduser().resolve()
    start_py = root / "start.py"
    if not start_py.exists():
        print(f"[launch] start.py not found in {root}", file=sys.stderr, flush=True)
        return 1

    prepend_runtime_paths(root)
    config = read_set_ini(root)
    devtype = config.get("devtype") or "cpu"
    web_address = config.get("web_address") or "127.0.0.1:9977"

    script_dir = Path(__file__).resolve().parent
    skill_root = script_dir.parents[2]
    runtime_helper = skill_root / "scripts" / "check-runtime.py"
    cuda_helper = script_dir / "check-cuda.py"

    print(f"[launch] repo_root={root}", flush=True)
    print(f"[launch] python={args.python}", flush=True)
    print(f"[launch] web_address={web_address}", flush=True)
    print(f"[launch] devtype={devtype}", flush=True)

    if devtype not in {"cpu", "cuda"}:
        print(f"[launch] warning: devtype={devtype!r} is not one of cpu/cuda", flush=True)

    if not args.skip_runtime_check:
        if not runtime_helper.exists():
            print("[launch] runtime helper missing", file=sys.stderr, flush=True)
            return 1
        rc = run_helper(args.python, runtime_helper, "--repo-root", str(root), cwd=root)
        if rc != 0:
            print("[launch] runtime preflight failed", file=sys.stderr, flush=True)
            return rc

    if devtype == "cuda" and not args.skip_cuda_check:
        if not cuda_helper.exists():
            print("[launch] CUDA helper missing", file=sys.stderr, flush=True)
            return 1
        rc = run_helper(args.python, cuda_helper, "--strict", cwd=root)
        if rc != 0:
            print("[launch] CUDA preflight failed", file=sys.stderr, flush=True)
            return rc
    elif devtype != "cuda":
        print("[launch] CPU mode selected; CUDA preflight skipped", flush=True)

    command = [args.python, "-u", start_py.name]
    print("[launch] command=" + " ".join(command), flush=True)
    if args.dry_run:
        return 0

    return subprocess.run(command, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
