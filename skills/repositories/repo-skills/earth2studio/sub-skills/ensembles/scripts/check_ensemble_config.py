#!/usr/bin/env python3
"""Check ensemble sizing and Async Zarr coordinate arithmetic offline."""
from __future__ import annotations

import argparse
import json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nensemble", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--nsteps", type=int, default=10)
    parser.add_argument("--parallel-coords", nargs="*", default=["ensemble", "time", "lead_time"])
    parser.add_argument("--shard-size", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    errors: list[str] = []
    if args.nensemble < 1: errors.append("nensemble must be >= 1")
    if args.nsteps < 0: errors.append("nsteps must be >= 0")
    batch = args.nensemble if args.batch_size is None else args.batch_size
    if batch < 1: errors.append("batch-size must be >= 1")
    if batch > args.nensemble: errors.append("batch-size must not exceed nensemble")
    required = {"ensemble", "time", "lead_time"}
    missing = sorted(required - set(args.parallel_coords))
    if missing: errors.append("parallel-coords missing required dimensions: " + ", ".join(missing))
    if args.shard_size is not None and args.shard_size < 1: errors.append("shard-size must be >= 1")
    batches = (args.nensemble + batch - 1) // batch if batch > 0 else None
    result = {"ok": not errors, "nensemble": args.nensemble, "batch_size": batch, "nsteps": args.nsteps, "batches": batches, "missing_parallel_coords": missing, "errors": errors, "offline": True}
    if args.json: print(json.dumps(result, sort_keys=True))
    else:
        print("ensemble configuration: " + ("PASS" if not errors else "FAIL"))
        for error in errors: print("ERROR:", error)
        if not errors: print(f"{batches} member batches; output has {args.nsteps + 1} lead-time positions")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
