#!/usr/bin/env python3
"""Build a safe Humanoid-Gym sim2sim command without launching MuJoCo.

This helper only prints the command and caveats. It does not load the policy
or start the viewer loop.
"""
from __future__ import annotations

import argparse
import shlex
import sys

DEFAULT_SCRIPT = "humanoid/scripts/sim2sim.py"


def build_command(args):
    parts = ["python", DEFAULT_SCRIPT, f"--load_model={args.policy}"]
    warnings = []
    if args.terrain:
        parts.append("--terrain")
    if args.notes:
        warnings.append("notes: {0}".format(args.notes))
    warnings.append("source sim2sim.py always opens a MuJoCo viewer and has no headless flag")
    warnings.append("validate assets/policy shape before trying the viewer rollout")
    return shlex.join(str(part) for part in parts), warnings


def build_parser():
    parser = argparse.ArgumentParser(
        description="Print a Humanoid-Gym sim2sim command without launching MuJoCo.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--load-model", "--load_model", "--policy", dest="policy", required=True, help="Path to the exported TorchScript policy.")
    parser.add_argument("--terrain", action="store_true", help="Select the terrain MJCF asset.")
    parser.add_argument("--notes", default="", help="Free-form notes to print with caveats.")
    return parser


def main():
    args = build_parser().parse_args()
    command, warnings = build_command(args)
    for warning in warnings:
        print("WARNING: {0}".format(warning), file=sys.stderr)
    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
