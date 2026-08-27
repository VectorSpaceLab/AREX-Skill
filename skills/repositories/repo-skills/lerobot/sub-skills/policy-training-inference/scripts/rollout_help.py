#!/usr/bin/env python3
"""Print a non-executing rollout safety plan and help command.

The script deliberately does not invoke lerobot-rollout: even setup can connect
to hardware, import plugins, or initialize visualization in some environments.
"""
from __future__ import annotations

import argparse
import shutil
import sys

RECORDING_STRATEGIES = {"sentry", "highlight", "episodic", "dagger"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strategy", choices=("base", "sentry", "highlight", "episodic", "dagger"), default="base")
    parser.add_argument("--inference", choices=("sync", "rtc"), default="sync")
    parser.add_argument("--duration", type=float, default=10.0, help="planned finite duration in seconds")
    parser.add_argument("--has-dataset", action="store_true", help="recording dataset is configured")
    parser.add_argument("--has-teleop", action="store_true", help="teleoperator is configured")
    parser.add_argument("--device", default="cpu", help="planned device; probe separately")
    args = parser.parse_args()
    if args.duration <= 0:
        parser.error("--duration must be finite and > 0 for the safety plan")
    if args.strategy == "base" and args.has_dataset:
        parser.error("base strategy does not record; omit --has-dataset or choose a recording strategy")
    if args.strategy != "base" and not args.has_dataset:
        parser.error(f"{args.strategy} strategy requires an approved recording dataset")
    if args.strategy == "dagger" and not args.has_teleop:
        parser.error("dagger strategy requires a teleoperator")
    executable = shutil.which("lerobot-rollout")
    print("Help command (not executed):")
    print("lerobot-rollout --help")
    print("\nPlan gates:")
    print(f"- strategy={args.strategy}; inference={args.inference}; finite duration={args.duration:g}s")
    print(f"- executable_on_PATH={bool(executable)}")
    print(f"- requested device={args.device}; use the policy environment probe before launch")
    print("- verify policy checkpoint, matching pre/postprocessors, feature names, image streams, and action shape")
    print("- verify robot calibration, workspace limits, emergency stop, and a human observer")
    print("- start with sync inference unless RTC support, queue horizon, and latency are measured")
    if args.strategy == "base":
        print("- base is autonomous/no-recording; keep recording flags and dataset unset")
    else:
        print("- approve local dataset writes and Hub credentials/uploads separately")
    print("\nThis script never imports robot plugins, starts rollout, opens cameras, downloads a checkpoint, or actuates hardware.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
