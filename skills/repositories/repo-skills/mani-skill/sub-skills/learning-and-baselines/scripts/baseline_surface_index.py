#!/usr/bin/env python3
"""Print a safe index of ManiSkill baseline-related reference material.

This helper is intentionally read-only: it never launches training, downloads,
or environment creation. It is meant to give a future agent a quick orientation
without opening the source repository.
"""

from __future__ import annotations

import argparse

SECTIONS = {
    "baselines": [
        "PPO, SAC, TD-MPC2, BC, ACT, Diffusion Policy, RFCL, RLPD",
        "reference file: references/baselines.md",
        "training-scale launchers are reference-only",
    ],
    "benchmark-tasks": [
        "small RL benchmark set for lower-compute comparison",
        "larger RL benchmark set documented as WIP / broader research coverage",
        "reference file: references/benchmark-tasks.md",
    ],
    "evaluation": [
        "no partial resets: ignore_terminations=True",
        "reconfigure on reset: reconfiguration_freq=1",
        "record metrics and read final_info for complete episodes",
        "reference file: references/evaluation.md",
    ],
    "troubleshooting": [
        "missing extras, wandb assumptions, backend mismatch, long runs",
        "reference file: references/troubleshooting.md",
    ],
    "data-generation": [
        "benchmark replay, demo-oriented flows, RL-to-demo helpers, motion-planning helpers",
        "reference file: references/data-generation.md",
        "details routed to trajectories-and-datasets for replay mechanics",
    ],
}


def emit(topic: str) -> str:
    items = SECTIONS[topic]
    body = [f"[{topic}]", *(f"- {item}" for item in items)]
    return "\n".join(body)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print a safe ManiSkill learning/baselines index.",
    )
    parser.add_argument(
        "--topic",
        choices=tuple(SECTIONS),
        action="append",
        help="Print only selected topic(s). May be repeated.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Use a one-line separator between sections.",
    )
    args = parser.parse_args()

    topics = args.topic or list(SECTIONS)
    sep = "\n" if args.compact else "\n\n"
    print(
        sep.join(emit(topic) for topic in topics)
        + "\n\nNote: this helper is reference-only and never trains."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
