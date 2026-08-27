#!/usr/bin/env python3
"""Safe local Ray availability smoke test for Data-Juicer."""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--num-cpus", type=int, default=1, help="CPUs to request from Ray")
    args = parser.parse_args()

    try:
        import ray
    except Exception as exc:  # pragma: no cover - smoke helper
        print(f"ray import failed: {exc}", file=sys.stderr)
        return 1

    try:
        ray.init(num_cpus=args.num_cpus, include_dashboard=False, ignore_reinit_error=True)
        print(f"ray_version={ray.__version__}")
        print(f"cluster_resources={ray.cluster_resources()}")
        print(f"initialized={ray.is_initialized()}")
    finally:
        try:
            ray.shutdown()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
