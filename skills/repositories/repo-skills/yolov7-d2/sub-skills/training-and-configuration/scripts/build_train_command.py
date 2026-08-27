#!/usr/bin/env python3
"""Build a YOLOv7-d2 training/evaluation command template."""
import argparse
import shlex

SCRIPT_BY_MODE = {
    "det": "train_det.py",
    "inseg": "train_inseg.py",
    "detr": "train_transformer.py",
    "custom": "train_custom_datasets.py",
    "lazy": "tools/lazyconfig_train_net.py",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a YOLOv7-d2 training/eval command template.")
    parser.add_argument("--mode", choices=sorted(SCRIPT_BY_MODE), required=True, help="Trainer route to use.")
    parser.add_argument("--config", required=True, help="User config path.")
    parser.add_argument("--num-gpus", type=int, default=1, help="GPUs per machine.")
    parser.add_argument("--eval-only", action="store_true", help="Add --eval-only.")
    parser.add_argument("--resume", action="store_true", help="Add --resume.")
    parser.add_argument("--num-machines", type=int, default=None)
    parser.add_argument("--machine-rank", type=int, default=None)
    parser.add_argument("--dist-url", default=None)
    parser.add_argument("--opts", nargs=argparse.REMAINDER, default=[], help="Trailing config overrides.")
    args = parser.parse_args()

    cmd = ["python", SCRIPT_BY_MODE[args.mode], "--config-file", args.config, "--num-gpus", str(args.num_gpus)]
    if args.eval_only:
        cmd.append("--eval-only")
    if args.resume:
        cmd.append("--resume")
    if args.num_machines is not None:
        cmd += ["--num-machines", str(args.num_machines)]
    if args.machine_rank is not None:
        cmd += ["--machine-rank", str(args.machine_rank)]
    if args.dist_url:
        cmd += ["--dist-url", args.dist_url]
    cmd += args.opts
    print(" ".join(shlex.quote(x) for x in cmd))
    if args.mode == "custom":
        print("# Ensure custom dataset registrations in your working launcher match DATASETS.TRAIN/TEST.")
    if args.mode == "lazy":
        print("# LazyConfig overrides use path.key=value syntax, not Yacs KEY VALUE pairs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
