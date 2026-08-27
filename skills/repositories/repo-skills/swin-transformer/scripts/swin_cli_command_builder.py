#!/usr/bin/env python3
"""Build Swin-Transformer command templates without executing them."""
from __future__ import annotations

import argparse
import shlex

WORKFLOW_TO_SCRIPT = {
    "supervised-train": "main.py",
    "supervised-eval": "main.py",
    "supervised-finetune": "main.py",
    "throughput": "main.py",
    "simmim-pretrain": "main_simmim_pt.py",
    "simmim-finetune": "main_simmim_ft.py",
    "simmim-eval": "main_simmim_ft.py",
    "moe-train": "main_moe.py",
    "moe-eval": "main_moe.py",
}


def q(x: str) -> str:
    return shlex.quote(str(x))


def main() -> int:
    ap = argparse.ArgumentParser(description="Print a torchrun command template for a Swin-Transformer workflow.")
    ap.add_argument("--workflow", required=True, choices=sorted(WORKFLOW_TO_SCRIPT))
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--data-path", required=True)
    ap.add_argument("--gpus", type=int, default=1)
    ap.add_argument("--nodes", type=int, default=1)
    ap.add_argument("--node-rank", default="0")
    ap.add_argument("--master-addr", default="127.0.0.1")
    ap.add_argument("--master-port", default="12345")
    ap.add_argument("--batch-size", type=int)
    ap.add_argument("--pretrained")
    ap.add_argument("--resume")
    ap.add_argument("--output", default="output")
    ap.add_argument("--tag")
    ap.add_argument("--zip", action="store_true")
    ap.add_argument("--cache-mode", choices=["no", "full", "part"])
    ap.add_argument("--accumulation-steps", type=int)
    ap.add_argument("--use-checkpoint", action="store_true")
    ap.add_argument("--disable-amp", action="store_true")
    ap.add_argument("--extra-opts", nargs="*", default=[], help="Additional config KEY VALUE pairs appended after --opts.")
    args = ap.parse_args()

    script = WORKFLOW_TO_SCRIPT[args.workflow]
    launcher = ["torchrun", "--nproc_per_node", str(args.gpus)]
    if args.nodes > 1 or args.workflow.startswith("moe"):
        launcher += ["--nnodes", str(args.nodes), "--node_rank", str(args.node_rank), "--master_addr", args.master_addr, "--master_port", args.master_port]
    cmd = launcher + [script, "--cfg", args.cfg, "--data-path", args.data_path, "--output", args.output]
    if args.batch_size:
        cmd += ["--batch-size", str(args.batch_size)]
    if args.tag:
        cmd += ["--tag", args.tag]
    if args.workflow in {"supervised-eval", "simmim-eval", "moe-eval"}:
        cmd.append("--eval")
        if args.resume:
            cmd += ["--resume", args.resume]
    if args.workflow in {"supervised-finetune", "simmim-finetune"} and args.pretrained:
        cmd += ["--pretrained", args.pretrained]
    if args.workflow == "throughput":
        cmd.append("--throughput")
    if args.zip:
        cmd.append("--zip")
    if args.cache_mode:
        cmd += ["--cache-mode", args.cache_mode]
    if args.accumulation_steps:
        cmd += ["--accumulation-steps", str(args.accumulation_steps)]
    if args.use_checkpoint:
        cmd.append("--use-checkpoint")
    if args.disable_amp:
        cmd.append("--disable_amp")
    if args.extra_opts:
        if len(args.extra_opts) % 2:
            raise SystemExit("--extra-opts must be KEY VALUE pairs")
        cmd += ["--opts"] + args.extra_opts

    print(" ".join(q(x) for x in cmd))
    print("\n# Review the data/checkpoint paths and optional backend requirements before executing this GPU/data-heavy command.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
