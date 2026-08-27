#!/usr/bin/env python3
"""Build a routed RL Baselines3 Zoo command without executing it.

This root helper is a lightweight command map. For workflow-specific validation,
use the nearest sub-skill helper (training, evaluation/artifacts, HPO, Hub,
plotting, or custom components). This script only chooses the installed-package
entry point and shell-quotes user-supplied arguments.
"""

from __future__ import annotations

import argparse
import json
import shlex
from typing import Any

TASKS = {
    "train": {
        "route": "sub-skills/training-cli/SKILL.md",
        "module": ["python", "-m", "rl_zoo3.train"],
        "console": ["rl_zoo3", "train"],
        "note": "Prefer module form for base installs; console form may require plotting extras.",
    },
    "enjoy": {
        "route": "sub-skills/evaluation-and-artifacts/SKILL.md",
        "module": ["python", "-m", "rl_zoo3.enjoy"],
        "console": ["rl_zoo3", "enjoy"],
        "note": "Add --no-render for headless evaluation.",
    },
    "plot-train": {
        "route": "sub-skills/plotting-benchmarking/SKILL.md",
        "module": ["rl_zoo3", "plot_train"],
        "console": ["rl_zoo3", "plot_train"],
        "note": "Requires plotting dependencies.",
    },
    "all-plots": {
        "route": "sub-skills/plotting-benchmarking/SKILL.md",
        "module": ["rl_zoo3", "all_plots"],
        "console": ["rl_zoo3", "all_plots"],
        "note": "Requires plotting dependencies and evaluation.npz files.",
    },
    "plot-from-file": {
        "route": "sub-skills/plotting-benchmarking/SKILL.md",
        "module": ["rl_zoo3", "plot_from_file"],
        "console": ["rl_zoo3", "plot_from_file"],
        "note": "Requires a postprocessed all_plots pickle.",
    },
    "benchmark": {
        "route": "sub-skills/plotting-benchmarking/SKILL.md",
        "module": ["python", "-m", "rl_zoo3.benchmark"],
        "console": ["python", "-m", "rl_zoo3.benchmark"],
        "note": "Use --test-mode --no-hub for bounded local smoke checks.",
    },
    "load-from-hub": {
        "route": "sub-skills/integrations-hub-tracking/SKILL.md",
        "module": ["python", "-m", "rl_zoo3.load_from_hub"],
        "console": ["python", "-m", "rl_zoo3.load_from_hub"],
        "note": "Plans a network command; do not execute without network/credential intent.",
    },
    "push-to-hub": {
        "route": "sub-skills/integrations-hub-tracking/SKILL.md",
        "module": ["python", "-m", "rl_zoo3.push_to_hub"],
        "console": ["python", "-m", "rl_zoo3.push_to_hub"],
        "note": "Plans upload/model-card packaging; validate local layout first.",
    },
    "record-video": {
        "route": "sub-skills/integrations-hub-tracking/SKILL.md",
        "module": ["python", "-m", "rl_zoo3.record_video"],
        "console": ["python", "-m", "rl_zoo3.record_video"],
        "note": "Video may require render_mode support and display/offscreen setup.",
    },
    "record-training": {
        "route": "sub-skills/integrations-hub-tracking/SKILL.md",
        "module": ["python", "-m", "rl_zoo3.record_training"],
        "console": ["python", "-m", "rl_zoo3.record_training"],
        "note": "Can call record_video for many checkpoints and may require ffmpeg.",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=sorted(TASKS))
    parser.add_argument("--style", choices=["module", "console"], default="module")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments to append after '--'")
    ns = parser.parse_args()

    extra = list(ns.args)
    if extra and extra[0] == "--":
        extra = extra[1:]

    task: dict[str, Any] = TASKS[ns.task]
    argv = list(task[ns.style]) + extra
    payload = {
        "command": shlex.join(argv),
        "argv": argv,
        "route": task["route"],
        "note": task["note"],
        "non_executing": True,
    }
    if ns.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload["command"])
        print(f"route: {payload['route']}")
        print(f"note: {payload['note']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
