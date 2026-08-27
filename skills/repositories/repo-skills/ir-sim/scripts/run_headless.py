#!/usr/bin/env python3
"""Run a bounded IR-SIM YAML scene without a desktop window.

The caller supplies the YAML path. The helper never searches a repository,
downloads data, or saves output unless explicitly requested with --snapshot.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Step a caller-provided IR-SIM scene in a headless backend."
    )
    parser.add_argument("config", type=Path, help="YAML scene path")
    parser.add_argument("--steps", type=int, default=10, help="maximum steps")
    parser.add_argument("--seed", type=int, default=None, help="IR-SIM seed")
    parser.add_argument(
        "--projection", choices=("2d", "3d"), default="2d", help="plot projection"
    )
    parser.add_argument(
        "--render", action="store_true", help="render each step using Agg"
    )
    parser.add_argument(
        "--snapshot", type=Path, help="optional PNG path after the final step"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.steps < 0:
        raise SystemExit("--steps must be non-negative")
    config = args.config.expanduser().resolve()
    if not config.is_file():
        raise SystemExit(f"YAML scene does not exist: {config}")

    import irsim

    env = irsim.make(
        str(config),
        projection=args.projection,
        display=False,
        save_ani=False,
        seed=args.seed,
    )
    try:
        for _ in range(args.steps):
            env.step()
            if args.render:
                env.render(interval=0.0)
            if env.done():
                break
        if args.snapshot is not None:
            from matplotlib import pyplot as plt

            output = args.snapshot.expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            plt.gcf().savefig(output, format="png", dpi=100)
            if not output.is_file():
                raise RuntimeError(f"snapshot was not created: {output}")
        print(
            f"ok steps={env.world_param.count} time={env.time:.2f} "
            f"status={env.status} done={env.done()}"
        )
        if args.snapshot is not None:
            print(f"snapshot={args.snapshot.expanduser().resolve()}")
    finally:
        env.close(ending_time=0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
