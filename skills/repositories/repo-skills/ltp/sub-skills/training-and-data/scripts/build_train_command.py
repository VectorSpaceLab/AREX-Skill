#!/usr/bin/env python3
"""Build safe LTP ltp_core train/eval command templates without running them."""
from __future__ import annotations

import argparse
import shlex

EXPERIMENTS = {"cws", "pos", "ner", "srl", "dep", "sdp", "multi", "multi_bi", "cls", "example"}
TRAINERS = {"default", "cpu", "gpu", "mps", "ddp", "ddp_sim"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit an ltp_core train/eval command template.")
    parser.add_argument("--mode", choices=["train", "eval"], required=True)
    parser.add_argument("--experiment", choices=sorted(EXPERIMENTS), help="experiment config to select")
    parser.add_argument("--trainer", choices=sorted(TRAINERS), default="default")
    parser.add_argument("--ckpt-path", help="checkpoint path; required for eval")
    parser.add_argument("--python", default="python", help="Python executable to show in the command")
    parser.add_argument("--overrides", nargs="*", default=[], help="extra Hydra overrides, e.g. seed=123 logger=null")
    args = parser.parse_args()

    if args.mode == "eval" and not args.ckpt_path:
        parser.error("--ckpt-path is required for --mode eval")

    module = "ltp_core.train" if args.mode == "train" else "ltp_core.eval"
    cmd = ["env", "TOKENIZERS_PARALLELISM=false", args.python, "-m", module]
    if args.experiment:
        cmd.append(f"experiment={args.experiment}")
    if args.trainer != "default":
        cmd.append(f"trainer={args.trainer}")
    if args.ckpt_path:
        cmd.append(f"ckpt_path={args.ckpt_path}")
    cmd.extend(args.overrides)

    print("Command template (review before running):")
    print(" ".join(shlex.quote(part) for part in cmd))
    print("\nNotes:")
    print("- This script did not run training or evaluation.")
    print("- Ensure training dependencies, config files, data paths, and model/backbone caches are available.")
    print("- Ask before long-running jobs, GPU/distributed launch, online loggers, or remote downloads.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
