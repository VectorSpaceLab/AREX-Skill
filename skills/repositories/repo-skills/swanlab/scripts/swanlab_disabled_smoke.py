#!/usr/bin/env python3
"""Credential-free SwanLab tracking smoke check.

Run this in any Python environment where `swanlab` is installed:
    python swanlab_disabled_smoke.py

The check uses mode="disabled" so it does not require an API key, network,
cloud account, dashboard service, or training data.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a minimal SwanLab disabled-mode tracking smoke check.")
    parser.add_argument("--project", default="swanlab-skill-smoke", help="Project name passed to swanlab.init.")
    parser.add_argument("--metric-key", default="loss", help="Metric key to log once.")
    parser.add_argument("--metric-value", type=float, default=0.1, help="Metric value to log once.")
    args = parser.parse_args(argv)

    try:
        import swanlab
    except Exception as exc:  # pragma: no cover - diagnostic user interface
        print(f"ERROR: cannot import swanlab: {exc}", file=sys.stderr)
        print("Install it with `pip install swanlab` in the target environment.", file=sys.stderr)
        return 2

    try:
        run = swanlab.init(project=args.project, mode="disabled")
        swanlab.log({args.metric_key: args.metric_value})
        if swanlab.run is not run:
            raise AssertionError("swanlab.run did not point at the active run")
        swanlab.finish()
        if swanlab.run is not None:
            raise AssertionError("swanlab.run did not reset to None after finish")
    except Exception as exc:  # pragma: no cover - diagnostic user interface
        print(f"ERROR: disabled-mode SwanLab smoke failed: {exc}", file=sys.stderr)
        return 1

    print("swanlab disabled-mode smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
