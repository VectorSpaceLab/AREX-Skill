#!/usr/bin/env python3
"""Run a bounded, headless IR-SIM lifecycle/render smoke check.

The default scene is created in a temporary directory, so this helper works
from an arbitrary current working directory and never depends on a repository
example or checkout-relative YAML file.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

# Set this before importing irsim/Matplotlib. An explicit caller value wins.
os.environ.setdefault("MPLBACKEND", "Agg")

import irsim  # noqa: E402
from matplotlib import pyplot as plt  # noqa: E402

TINY_WORLD = """\
world:
  height: 4
  width: 4
  step_time: 0.1
  sample_time: 0.1
  offset: [0, 0]
  control_mode: auto
  collision_mode: stop
  plot:
    show_title: false
robot:
  kinematics: {name: diff}
  shape: {name: circle, radius: 0.15}
  state: [0.5, 0.5, 0]
  goal: [3.5, 0.5, 0]
  behavior: {name: dash}
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny IR-SIM step/render/close smoke check in a headless "
            "Matplotlib backend."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Existing YAML scene to use; otherwise a temporary tiny scene is used.",
    )
    parser.add_argument(
        "--projection",
        choices=("2d", "3d"),
        default="2d",
        help="Environment projection (default: 2d).",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=2,
        help="Maximum number of steps/render calls (default: 2).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="IR-SIM seed for the smoke run (default: 7).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional explicit path for one PNG screenshot after the smoke run.",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    if args.steps < 0:
        raise ValueError("--steps must be non-negative")

    env = None
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    try:
        if args.config is None:
            temp_dir = tempfile.TemporaryDirectory(prefix="irsim-render-smoke-")
            config = Path(temp_dir.name) / "tiny_world.yaml"
            config.write_text(TINY_WORLD, encoding="utf-8")
        else:
            config = args.config.expanduser().resolve()
            if not config.is_file():
                raise FileNotFoundError(f"YAML config does not exist: {config}")

        env = irsim.make(
            str(config),
            projection=args.projection,
            display=False,
            save_ani=False,
            log_level="CRITICAL",
            seed=args.seed,
        )

        for _ in range(args.steps):
            env.step()
            env.render(interval=0.0)
            if env.done():
                break

        if args.output is not None:
            output = args.output.expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            # This is an explicit-path smoke output. EnvBase.save_figure writes
            # under its configured path manager, so save the current Matplotlib
            # figure directly for the caller-requested path instead.
            plt.gcf().savefig(output, format="png", dpi=100)
            if not output.is_file():
                raise RuntimeError(f"IR-SIM did not create screenshot: {output}")

        print(
            f"ok projection={args.projection} steps={env.world_param.count} "
            f"time={env.time:.2f} status={env.status}"
        )
        if args.output is not None:
            print(f"screenshot={args.output.expanduser().resolve()}")
        return 0
    finally:
        if env is not None:
            env.close(ending_time=0)
        if temp_dir is not None:
            temp_dir.cleanup()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
