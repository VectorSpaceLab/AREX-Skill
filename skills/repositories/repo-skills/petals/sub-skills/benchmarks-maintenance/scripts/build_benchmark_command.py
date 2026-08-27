#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex

DTYPES = ("float32", "float16", "bfloat16", "auto")


def pos(v):
    value = int(v)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def nproc(v):
    if v == "n_gpus":
        return v
    pos(v)
    return v


def add_common(p):
    p.add_argument("--model", required=True)
    p.add_argument("--initial-peer", action="append", dest="peers", default=[])
    p.add_argument("--allow-public-swarm", action="store_true")
    p.add_argument("--torch-dtype", choices=DTYPES)
    p.add_argument("--n-processes", type=nproc)
    p.add_argument("--seq-len", type=pos)
    p.add_argument("--warmup-steps", type=pos)
    p.add_argument("--smoke", action="store_true")


def main():
    p = argparse.ArgumentParser(description="Build Petals benchmark command templates. This tool prints only and never executes.")
    sub = p.add_subparsers(dest="fam", required=True)
    inf = sub.add_parser("inference")
    add_common(inf)
    fwd = sub.add_parser("forward")
    add_common(fwd)
    fwd.add_argument("--batch-size", type=pos)
    fwd.add_argument("--n-steps", type=pos)
    tr = sub.add_parser("training")
    add_common(tr)
    tr.add_argument("--device")
    tr.add_argument("--task", choices=("cls", "causal_lm"), default="cls")
    tr.add_argument("--batch-size", type=pos)
    tr.add_argument("--pre-seq-len", type=pos)
    tr.add_argument("--n-steps", type=pos)
    args = p.parse_args()
    if not args.peers and not args.allow_public_swarm:
        p.error("provide --initial-peer or --allow-public-swarm")
    cmd = ["python", "scripts/run_petals_benchmark.py", args.fam, "--model", args.model]
    if args.peers:
        cmd += ["--initial_peers", *args.peers]
    cmd += ["--torch_dtype", args.torch_dtype or "float32", "--n_processes", args.n_processes or "1"]
    if args.fam == "inference":
        cmd += ["--seq_len", str(args.seq_len or (3 if args.smoke else 2048)), "--warmup_steps", str(args.warmup_steps or 1)]
    elif args.fam == "forward":
        batch = args.batch_size or (3 if args.smoke else None)
        if batch is None:
            p.error("forward requires --batch-size unless --smoke")
        cmd += [
            "--seq_len",
            str(args.seq_len or (3 if args.smoke else 128)),
            "--batch_size",
            str(batch),
            "--n_steps",
            str(args.n_steps or (1 if args.smoke else 100)),
            "--warmup_steps",
            str(args.warmup_steps or 1),
        ]
    else:
        batch = args.batch_size or (3 if args.smoke else None)
        if batch is None:
            p.error("training requires --batch-size unless --smoke")
        cmd += [
            "--device",
            args.device or "cpu",
            "--task",
            args.task,
            "--seq_len",
            str(args.seq_len or (3 if args.smoke else 128)),
            "--pre_seq_len",
            str(args.pre_seq_len or (1 if args.smoke else 16)),
            "--batch_size",
            str(batch),
            "--n_steps",
            str(args.n_steps or (1 if args.smoke else 10)),
            "--warmup_steps",
            str(args.warmup_steps or 1),
        ]
    print(shlex.join(cmd))
    print("# CHECK: print-only; confirm model/cache/network/timeout/cleanup before execution")


if __name__ == "__main__":
    main()
