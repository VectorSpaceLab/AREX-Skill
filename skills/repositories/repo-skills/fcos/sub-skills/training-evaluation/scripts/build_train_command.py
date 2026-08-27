#!/usr/bin/env python3
"""Build an FCOS training command without running it."""
from __future__ import annotations

import argparse
import shlex


def q(x: str) -> str:
    return shlex.quote(str(x))


def main() -> int:
    p = argparse.ArgumentParser(description="Print an FCOS training command")
    p.add_argument("--config-file", required=True)
    p.add_argument("--gpus", type=int, default=1, help="Number of processes/GPUs")
    p.add_argument("--master-port", default="$((RANDOM + 10000))")
    p.add_argument("--output-dir")
    p.add_argument("--train-script", default="train_net.py", help="Path to a compatible FCOS train entry script")
    p.add_argument("--skip-test", action="store_true")
    p.add_argument("--override", nargs="*", default=[], help="Additional cfg merge_from_list tokens")
    args = p.parse_args()
    if args.gpus < 1:
        p.error("--gpus must be >= 1")
    opts = list(args.override)
    if args.output_dir:
        opts += ["OUTPUT_DIR", args.output_dir]
    base = ["python"]
    if args.gpus > 1:
        base += ["-m", "torch.distributed.launch", f"--nproc_per_node={args.gpus}", f"--master_port={args.master_port}"]
    base += [args.train_script, "--config-file", args.config_file]
    if args.skip_test:
        base.append("--skip-test")
    base += opts
    print(" ".join(q(x) for x in base))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
