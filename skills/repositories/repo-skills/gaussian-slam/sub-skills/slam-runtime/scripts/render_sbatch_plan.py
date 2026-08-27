#!/usr/bin/env python3
"""Render a reviewable SLURM plan without submitting or running anything."""
from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

CONFIG_DIRS = {
    "Replica": "Replica",
    "TUM_RGBD": "TUM_RGBD",
    "ScanNet": "ScanNet",
    "ScanNetPP": "scannetpp",
}


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Print a safe Gaussian-SLAM SLURM batch plan; never submits or starts a job."
    )
    p.add_argument("--dataset", required=True, choices=sorted(CONFIG_DIRS))
    p.add_argument("--scene", action="append", required=True, help="scene/config stem; repeat for array elements")
    p.add_argument("--input-root", required=True, help="root joined with each scene name")
    p.add_argument("--output-root", required=True, help="root for logs and per-scene outputs")
    p.add_argument("--config-root", default="configs")
    p.add_argument("--experiment-name", default="reproduce")
    p.add_argument("--partition", default="gpu")
    p.add_argument("--gpus", type=int, default=1)
    p.add_argument("--cpus", type=int, default=12)
    p.add_argument("--time", default="24:00:00")
    p.add_argument("--python", default="python", help="Python command to print in the plan")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--conda-setup", default=None, help="optional path printed as a commented source line")
    p.add_argument("--check-files", action="store_true", help="check local config paths; never downloads")
    return p


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    if args.gpus < 1 or args.cpus < 1:
        print("error: --gpus and --cpus must be positive", file=sys.stderr)
        return 2
    scenes = args.scene
    config_dir = Path(args.config_root) / CONFIG_DIRS[args.dataset]
    missing = [config_dir / f"{scene}.yaml" for scene in scenes if not (config_dir / f"{scene}.yaml").is_file()]
    if args.check_files and missing:
        for path in missing:
            print(f"missing config: {path}", file=sys.stderr)
        return 2

    output_root = shlex.quote(args.output_root)
    repo_root = shlex.quote(args.repo_root)
    input_root = shlex.quote(args.input_root)
    config_root = shlex.quote(args.config_root)
    experiment = shlex.quote(args.experiment_name)
    partition = shlex.quote(args.partition)
    py = shlex.quote(args.python)
    array_end = len(scenes) - 1
    print("# Gaussian-SLAM plan: review only; this output does not submit or execute")
    print("#!/usr/bin/env bash")
    print(f"#SBATCH --output={args.output_root}/logs/%A_%a.log")
    print(f"#SBATCH --error={args.output_root}/logs/%A_%a.log")
    print("#SBATCH -N 1")
    print("#SBATCH -n 1")
    print(f"#SBATCH --gpus-per-node={args.gpus}")
    print(f"#SBATCH --partition={args.partition}")
    print(f"#SBATCH --cpus-per-task={args.cpus}")
    print(f"#SBATCH --time={args.time}")
    print(f"#SBATCH --array=0-{array_end}")
    print()
    print("set -euo pipefail")
    print(f"cd {repo_root}")
    if args.conda_setup:
        print(f"# source {shlex.quote(args.conda_setup)}")
    else:
        print("# source <path-to-conda.sh>")
    print("# Activate the prepared Gaussian-SLAM environment using your site policy.")
    print("mkdir -p " + output_root + "/logs")
    print("scenes=(")
    for scene in scenes:
        print(f"  {shlex.quote(scene)}")
    print(")")
    print('scene="${scenes[$SLURM_ARRAY_TASK_ID]}"')
    print('echo "Running $scene on $(hostname) at $(date)"')
    print("DISABLE_WANDB=true " + py + " run_slam.py \\")
    print(f"  {config_root}/{CONFIG_DIRS[args.dataset]}/\"${{scene}}\".yaml \\")
    print(f"  --input_path {input_root}/\"${{scene}}\" \\")
    print(f"  --output_path {output_root}/{args.dataset}/{experiment}/\"${{scene}}\" \\")
    print(f"  --group_name {experiment}")
    print()
    print("# Review config paths, scene roots, resources, and environment activation before manual sbatch submission.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
