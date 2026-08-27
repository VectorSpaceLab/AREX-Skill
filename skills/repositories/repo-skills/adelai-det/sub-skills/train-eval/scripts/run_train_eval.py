#!/usr/bin/env python3
"""Validated launcher for AdelaiDet training/evaluation.

This wrapper composes the repository's tools/train_net.py command and performs
path checks before execution. Use --dry-run to inspect the command.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


def existing_path(base: Path, value: str, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    if not path.exists():
        raise SystemExit(f"{label} does not exist: {path}")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AdelaiDet train/eval with preflight checks")
    parser.add_argument("--repo-root", required=True, help="AdelaiDet source checkout root")
    parser.add_argument("--config", required=True, help="Config YAML path, absolute or relative to repo root")
    parser.add_argument("--num-gpus", type=int, default=1)
    parser.add_argument("--num-machines", type=int, default=1)
    parser.add_argument("--machine-rank", type=int, default=0)
    parser.add_argument("--dist-url", default="tcp://127.0.0.1:50152")
    parser.add_argument("--eval-only", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--model-weights", help="Append MODEL.WEIGHTS override")
    parser.add_argument("--opts", nargs=argparse.REMAINDER, default=[], help="Extra config KEY VALUE pairs")
    parser.add_argument("--dry-run", action="store_true", help="Print command without running it")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo_root).resolve()
    if not repo.is_dir():
        raise SystemExit(f"repo root is not a directory: {repo}")
    train_py = repo / "tools" / "train_net.py"
    if not train_py.exists():
        raise SystemExit(f"missing AdelaiDet training script: {train_py}")
    config = existing_path(repo, args.config, "config")

    opts = list(args.opts)
    if args.model_weights:
        weights = existing_path(repo, args.model_weights, "model weights")
        opts.extend(["MODEL.WEIGHTS", str(weights)])

    cmd = [
        sys.executable,
        str(train_py),
        "--num-gpus",
        str(args.num_gpus),
        "--num-machines",
        str(args.num_machines),
        "--machine-rank",
        str(args.machine_rank),
        "--dist-url",
        args.dist_url,
        "--config-file",
        str(config),
    ]
    if args.eval_only:
        cmd.append("--eval-only")
    if args.resume:
        cmd.append("--resume")
    cmd.extend(opts)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
    print(" ".join(shlex.quote(part) for part in cmd))
    if args.dry_run:
        return 0
    return subprocess.call(cmd, cwd=str(repo), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
