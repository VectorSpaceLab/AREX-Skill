#!/usr/bin/env python3
"""Render safe UniAD train/eval/SLURM commands without executing them."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

WORKFLOWS = {
    "bevformer": "projects/configs/bevformer/base_bevformer.py",
    "stage1": "projects/configs/stage1_track_map/base_track_map.py",
    "stage2": "projects/configs/stage2_e2e/base_e2e.py",
}


def work_dir_for(config: str) -> str:
    stem = str(Path(config).with_suffix(""))
    return stem.replace("configs", "work_dirs") + "/"


def gpus_per_node(gpus: int) -> int:
    return gpus if gpus < 8 else 8


def render(args: argparse.Namespace) -> dict:
    config = args.config or WORKFLOWS[args.workflow]
    work_dir = args.work_dir or work_dir_for(config)
    gpn = gpus_per_node(args.gpus)
    nnodes = max(1, args.gpus // gpn)
    extra = " ".join(args.extra) if args.extra else ""

    if args.mode == "train":
        command = (
            f'PYTHONPATH="$(pwd)":$PYTHONPATH torchrun '
            f'--nproc_per_node={gpn} --master_addr=${{MASTER_ADDR:-127.0.0.1}} '
            f'--master_port=${{MASTER_PORT:-28596}} --nnodes={nnodes} --node_rank=${{RANK:-0}} '
            f'tools/train.py {config} --launcher pytorch --deterministic --work-dir {work_dir}'
        )
        if extra:
            command += f" {extra}"
    elif args.mode == "eval":
        if not args.checkpoint:
            raise SystemExit("--checkpoint is required for eval mode")
        command = (
            f'PYTHONPATH="$(pwd)":$PYTHONPATH torchrun '
            f'--nproc_per_node={gpn} --master_port=${{MASTER_PORT:-28596}} '
            f'tools/test.py {config} {args.checkpoint} --launcher pytorch --eval bbox --show-dir {work_dir}'
        )
        if args.out:
            command += f" --out {args.out}"
        if extra:
            command += f" {extra}"
    elif args.mode == "slurm-train":
        if not args.partition:
            raise SystemExit("--partition is required for slurm-train mode")
        command = (
            f'srun -p {args.partition} --job-name=uniad_train --gres=gpu:{gpn} '
            f'--ntasks={args.gpus} --ntasks-per-node={gpn} --cpus-per-task=${{CPUS_PER_TASK:-5}} '
            f'--kill-on-bad-exit=1 ${{SRUN_ARGS:-}} '
            f'python -W ignore -u tools/train.py {config} --work-dir {work_dir} --launcher=slurm'
        )
        if extra:
            command += f" {extra}"
    elif args.mode == "slurm-eval":
        if not args.partition or not args.checkpoint:
            raise SystemExit("--partition and --checkpoint are required for slurm-eval mode")
        command = (
            f'srun -p {args.partition} --job-name=uniad_eval --gres=gpu:{gpn} '
            f'--ntasks={args.gpus} --ntasks-per-node={gpn} --cpus-per-task=${{CPUS_PER_TASK:-5}} '
            f'--kill-on-bad-exit=1 ${{SRUN_ARGS:-}} '
            f'python -W ignore -u tools/test.py {config} {args.checkpoint} '
            f'--launcher=slurm --eval bbox --show-dir {work_dir}'
        )
        if args.out:
            command += f" --out {args.out}"
        if extra:
            command += f" {extra}"
    else:
        raise AssertionError(args.mode)

    return {
        "mode": args.mode,
        "workflow": args.workflow,
        "config": config,
        "work_dir": work_dir,
        "gpus": args.gpus,
        "gpus_per_node": gpn,
        "nnodes": nnodes,
        "command": command,
        "notes": [
            "This helper renders commands only; it does not execute UniAD.",
            "Run from the UniAD repository root so PYTHONPATH=$(pwd) exposes projects.mmdet3d_plugin.",
            "Full evaluation/training requires prepared nuScenes data, checkpoints, and a compatible CUDA/OpenMMLab runtime.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=["train", "eval", "slurm-train", "slurm-eval"])
    parser.add_argument("--workflow", default="stage1", choices=sorted(WORKFLOWS))
    parser.add_argument("--config", help="Override config path instead of using the workflow default")
    parser.add_argument("--checkpoint", help="Checkpoint path required for eval modes")
    parser.add_argument("--gpus", type=int, default=8)
    parser.add_argument("--partition", help="SLURM partition for slurm-* modes")
    parser.add_argument("--work-dir", help="Override rendered work_dir")
    parser.add_argument("--out", help="Optional results pickle path for eval modes")
    parser.add_argument("--extra", nargs=argparse.REMAINDER, help="Extra args appended to train.py/test.py")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of plain command")
    args = parser.parse_args()
    if args.gpus < 1:
        raise SystemExit("--gpus must be >= 1")
    rendered = render(args)
    if args.json:
        print(json.dumps(rendered, indent=2))
    else:
        print(rendered["command"])
        for note in rendered["notes"]:
            print(f"# {note}")


if __name__ == "__main__":
    main()
