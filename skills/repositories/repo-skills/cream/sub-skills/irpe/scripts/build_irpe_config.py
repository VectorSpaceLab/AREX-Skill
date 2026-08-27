#!/usr/bin/env python3
"""Print a ready-to-copy Python snippet for an iRPE configuration.

This helper does not import the source repository. It only renders the config
call that future agents can paste into the relevant DeiT or DETR integration.
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Print an iRPE config snippet")
    parser.add_argument("--ratio", type=float, default=1.9)
    parser.add_argument("--method", default="product")
    parser.add_argument("--mode", default="ctx")
    parser.add_argument("--shared-head", action="store_true")
    parser.add_argument("--skip", type=int, default=0)
    parser.add_argument("--rpe-on", default="k")
    parser.add_argument("--head-dim", type=int, default=64)
    parser.add_argument("--num-heads", type=int, default=12)
    args = parser.parse_args()

    print("from irpe import get_rpe_config, build_rpe")
    print("rpe_config = get_rpe_config(")
    print(f"    ratio={args.ratio!r},")
    print(f"    method={args.method!r},")
    print(f"    mode={args.mode!r},")
    print(f"    shared_head={args.shared_head!r},")
    print(f"    skip={args.skip!r},")
    print(f"    rpe_on={args.rpe_on!r},")
    print(")")
    print(f"rpe_q, rpe_k, rpe_v = build_rpe(rpe_config, head_dim={args.head_dim}, num_heads={args.num_heads})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
