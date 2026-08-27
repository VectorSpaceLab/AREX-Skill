#!/usr/bin/env python3
"""Build safe OpenPCDet workflow commands from structured inputs.

By default this prints commands only. Add `--execute` to run the command in the
provided checkout. This avoids copying large repository scripts into the skill
while giving future agents a self-contained, checked launcher.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

ENTRYPOINTS = {
    "train": "tools/train.py",
    "test": "tools/test.py",
    "demo": "tools/demo.py",
    "kitti-infos": "pcdet/datasets/kitti/kitti_dataset.py",
    "custom-infos": "pcdet/datasets/custom/custom_dataset.py",
    "nuscenes-infos": "pcdet/datasets/nuscenes/nuscenes_dataset.py",
    "waymo-infos": "pcdet/datasets/waymo/waymo_dataset.py",
    "lyft-infos": "pcdet/datasets/lyft/lyft_dataset.py",
    "once-infos": "pcdet/datasets/once/once_dataset.py",
    "pandaset-infos": "pcdet/datasets/pandaset/pandaset_dataset.py",
    "argo2-infos": "pcdet/datasets/argo2/argo2_dataset.py",
}

DATASET_FUNC = {
    "kitti-infos": "create_kitti_infos",
    "custom-infos": "create_custom_infos",
    "nuscenes-infos": "create_nuscenes_infos",
    "waymo-infos": "create_waymo_infos",
    "lyft-infos": "create_lyft_infos",
    "once-infos": "create_once_infos",
    "pandaset-infos": "create_pandaset_infos",
}


def q(parts: list[str]) -> str:
    return " ".join(shlex.quote(x) for x in parts)


def require_entry(repo: Path, mode: str) -> Path:
    script = repo / ENTRYPOINTS[mode]
    if not script.exists():
        raise SystemExit(f"Expected OpenPCDet entrypoint is missing for {mode}: {ENTRYPOINTS[mode]}")
    return script


def path_for_workdir(path: Path, workdir: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(workdir))
    except ValueError:
        return str(resolved)


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan or execute an OpenPCDet command")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="OpenPCDet checkout root")
    parser.add_argument("--python", default=sys.executable, help="Python executable for the target environment")
    parser.add_argument("--mode", required=True, choices=sorted(ENTRYPOINTS), help="Workflow to plan")
    parser.add_argument("--cfg", type=Path, help="Config YAML for train/test/demo/dataset info modes")
    parser.add_argument("--ckpt", type=Path, help="Checkpoint path for test/demo or train resume")
    parser.add_argument("--data-path", type=Path, help="Point-cloud path for demo")
    parser.add_argument("--ext", default=None, choices=[".bin", ".npy"], help="Demo input extension")
    parser.add_argument("--batch-size", type=int, help="Override batch size")
    parser.add_argument("--workers", type=int, help="Dataloader workers")
    parser.add_argument("--extra-tag", help="Experiment tag")
    parser.add_argument("--launcher", choices=["none", "pytorch", "slurm"], help="Distributed launcher")
    parser.add_argument("--eval-all", action="store_true", help="For test mode, evaluate all checkpoints")
    parser.add_argument("--save-to-file", action="store_true", help="For test/train eval, write result files")
    parser.add_argument("--set", dest="set_cfgs", nargs=argparse.REMAINDER, default=None, help="Trailing cfg overrides")
    parser.add_argument("--execute", action="store_true", help="Actually run instead of printing")
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not (repo / "pcdet").is_dir():
        raise SystemExit(f"--repo is not an OpenPCDet checkout: {repo}")
    script = require_entry(repo, args.mode)

    if args.mode in {"train", "test", "demo"}:
        workdir = repo / "tools"
        cmd = [args.python, script.name]
        if not args.cfg:
            raise SystemExit(f"--cfg is required for {args.mode}")
        cfg_path = args.cfg if args.cfg.is_absolute() else (repo / args.cfg)
        cmd += ["--cfg_file", path_for_workdir(cfg_path, workdir)]
    else:
        workdir = repo
        cmd = [args.python, str(script.relative_to(repo))]

    if args.mode == "train":
        if args.batch_size is not None:
            cmd += ["--batch_size", str(args.batch_size)]
        if args.ckpt:
            cmd += ["--ckpt", str(args.ckpt)]
        if args.workers is not None:
            cmd += ["--workers", str(args.workers)]
        if args.extra_tag:
            cmd += ["--extra_tag", args.extra_tag]
        if args.launcher:
            cmd += ["--launcher", args.launcher]
        if args.save_to_file:
            cmd += ["--save_to_file"]
    elif args.mode == "test":
        if args.ckpt:
            cmd += ["--ckpt", str(args.ckpt)]
        if args.batch_size is not None:
            cmd += ["--batch_size", str(args.batch_size)]
        if args.workers is not None:
            cmd += ["--workers", str(args.workers)]
        if args.extra_tag:
            cmd += ["--extra_tag", args.extra_tag]
        if args.launcher:
            cmd += ["--launcher", args.launcher]
        if args.eval_all:
            cmd += ["--eval_all"]
        if args.save_to_file:
            cmd += ["--save_to_file"]
    elif args.mode == "demo":
        if not args.ckpt:
            raise SystemExit("--ckpt is required for demo")
        if not args.data_path:
            raise SystemExit("--data-path is required for demo")
        cmd += ["--ckpt", str(args.ckpt), "--data_path", str(args.data_path)]
        if args.ext:
            cmd += ["--ext", args.ext]
    else:
        if args.mode == "argo2-infos":
            # Argo2 has a repo-specific no-arg main block that reads paths from its config/evidence.
            pass
        else:
            func = DATASET_FUNC.get(args.mode)
            if func:
                cmd.append(func)
            if args.cfg:
                cfg_path = args.cfg if args.cfg.is_absolute() else (repo / args.cfg)
                cmd += ["--cfg_file", path_for_workdir(cfg_path, workdir)]

    if args.set_cfgs:
        cmd += ["--set"] + args.set_cfgs

    if workdir == repo:
        print(q(cmd))
    else:
        print(f"cd {shlex.quote(str(workdir))} && {q(cmd)}")
    if not args.execute:
        return 0
    return subprocess.call(cmd, cwd=str(workdir))


if __name__ == "__main__":
    raise SystemExit(main())
