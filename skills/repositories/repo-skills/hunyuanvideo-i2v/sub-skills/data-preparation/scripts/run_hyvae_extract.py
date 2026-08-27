#!/usr/bin/env python3
"""Build or execute the HunyuanVideo-I2V VAE latent extraction command.

Safe by default: prints commands unless --execute is passed.
"""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def _shell_quote(command: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or execute the HunyuanVideo-I2V latent extraction launcher")
    parser.add_argument("--repo-root", default=".", help="Path to the HunyuanVideo-I2V checkout")
    parser.add_argument("--config", default="hyvideo/hyvae_extract/vae.yaml", help="Extraction YAML config path")
    parser.add_argument("--host-gpu-num", type=int, default=1, help="Number of local ranks to launch")
    parser.add_argument("--python", default=sys.executable, help="Python executable to use")
    parser.add_argument("--execute", action="store_true", help="Actually run the commands instead of printing them")
    parser.add_argument("--dry-run", action="store_true", help="Print the commands without executing them (default behavior)")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    run_script = repo_root / "hyvideo" / "hyvae_extract" / "run.py"
    config = Path(args.config)
    if not config.is_absolute():
        config = repo_root / config
    if not run_script.exists():
        raise FileNotFoundError(f"extractor script not found: {run_script}")
    if not config.exists():
        raise FileNotFoundError(f"config not found: {config}")

    commands: list[tuple[list[str], dict[str, str]]] = []
    for local_rank in range(args.host_gpu_num):
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{repo_root}:{env.get('PYTHONPATH', '')}"
        env["HOST_GPU_NUM"] = str(args.host_gpu_num)
        env["CUDA_VISIBLE_DEVICES"] = str(local_rank)
        cmd = [args.python, "-u", str(run_script), "--local_rank", str(local_rank), "--config", str(config)]
        commands.append((cmd, env))

    for cmd, env in commands:
        prefix = f"HOST_GPU_NUM={env['HOST_GPU_NUM']} CUDA_VISIBLE_DEVICES={env['CUDA_VISIBLE_DEVICES']} PYTHONPATH={repo_root}"
        print(prefix, _shell_quote(cmd))

    if not args.execute:
        return 0

    procs = []
    for cmd, env in commands:
        procs.append(subprocess.Popen(cmd, cwd=str(repo_root), env=env))
    failures = 0
    for proc in procs:
        rc = proc.wait()
        if rc != 0:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
