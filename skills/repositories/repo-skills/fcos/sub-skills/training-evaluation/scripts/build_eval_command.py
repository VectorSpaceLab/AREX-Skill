#!/usr/bin/env python3
"""Build an FCOS evaluation command without running it."""
from __future__ import annotations

import argparse
import shlex


def q(x: str) -> str:
    return shlex.quote(str(x))


def main() -> int:
    p = argparse.ArgumentParser(description="Print an FCOS evaluation command")
    p.add_argument("--config-file", required=True)
    p.add_argument("--weights", help="MODEL.WEIGHT value")
    p.add_argument("--ims-per-batch", type=int, help="TEST.IMS_PER_BATCH override")
    p.add_argument("--output-dir")
    p.add_argument("--gpus", type=int, default=1)
    p.add_argument("--master-port", default="$((RANDOM + 10000))")
    p.add_argument("--test-script", default="test_net.py", help="Path to a compatible FCOS test entry script")
    p.add_argument("--override", nargs="*", default=[], help="Additional cfg merge_from_list tokens")
    args = p.parse_args()
    if args.gpus < 1:
        p.error("--gpus must be >= 1")
    opts = list(args.override)
    if args.weights:
        opts += ["MODEL.WEIGHT", args.weights]
    if args.ims_per_batch is not None:
        opts += ["TEST.IMS_PER_BATCH", str(args.ims_per_batch)]
    if args.output_dir:
        opts += ["OUTPUT_DIR", args.output_dir]
    base = ["python"]
    if args.gpus > 1:
        base += ["-m", "torch.distributed.launch", f"--nproc_per_node={args.gpus}", f"--master_port={args.master_port}"]
    base += [args.test_script, "--config-file", args.config_file]
    base += opts
    print(" ".join(q(x) for x in base))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
