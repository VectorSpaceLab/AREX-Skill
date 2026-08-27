#!/usr/bin/env python3
"""Check simple ColossalAI hybrid parallelism divisibility."""
import argparse
import math


def main():
    ap = argparse.ArgumentParser(description="Validate TP/PP/SP/EP sizing against world size.")
    ap.add_argument("--world-size", type=int, required=True)
    ap.add_argument("--tp", type=int, default=1)
    ap.add_argument("--pp", type=int, default=1)
    ap.add_argument("--sp", type=int, default=1)
    ap.add_argument("--ep", type=int, default=1)
    args = ap.parse_args()
    factors = [args.tp, args.pp, args.sp, args.ep]
    if any(x < 1 for x in factors + [args.world_size]):
        raise SystemExit("all sizes must be positive")
    product = math.prod(factors)
    print(f"world_size={args.world_size} tp={args.tp} pp={args.pp} sp={args.sp} ep={args.ep} product={product}")
    if args.world_size % product:
        raise SystemExit(f"invalid: world size is not divisible by topology product; remainder={args.world_size % product}")
    print(f"valid: data_parallel_remainder={args.world_size // product}")


if __name__ == "__main__":
    main()
