#!/usr/bin/env python3
"""Print a safe Isaac Lab RL train/play command skeleton and library metadata."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LIBRARY_EXTRAS = {
    "rl_games": {"package": "isaaclab_rl", "extra": "rl_games"},
    "rsl_rl": {"package": "isaaclab_rl", "extra": "rsl_rl"},
    "sb3": {"package": "isaaclab_rl", "extra": "sb3"},
    "skrl": {"package": "isaaclab_rl", "extra": "skrl"},
    "rlinf": {"package": "isaaclab_contrib", "extra": "rlinf"},
}

COMMON_FLAGS = [
    "--task TASK",
    "--agent AGENT",
    "--seed SEED",
    "--num_envs N",
    "--distributed",
    "--max_iterations N",
    "--video",
    "--video_length N",
    "--video_interval N",
    "--checkpoint PATH",
    "--load_run RUN_NAME",
    "--export_io_descriptors",
]


@dataclass
class CommandSkeleton:
    action: str
    rl_library: str
    task: str | None
    preset_tokens: list[str]
    flags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "rl_library": self.rl_library,
            "task": self.task,
            "preset_tokens": self.preset_tokens,
            "flags": self.flags,
            "install_extra": LIBRARY_EXTRAS[self.rl_library],
            "command": self.command_line(),
        }

    def command_line(self) -> str:
        parts = ["./isaaclab.sh", self.action, "--rl_library", self.rl_library]
        if self.task:
            parts.extend(["--task", self.task])
        parts.extend(self.preset_tokens)
        parts.extend(self.flags)
        return " ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Isaac Lab RL wrapper command skeletons.")
    parser.add_argument("action", choices=("train", "play"), help="Wrapper action to summarize.")
    parser.add_argument("--rl_library", choices=sorted(LIBRARY_EXTRAS), required=True)
    parser.add_argument("--task", type=str, default=None)
    parser.add_argument("--preset", action="append", default=[], help="Typed preset token such as physics=newton_mjwarp.")
    parser.add_argument("--flag", action="append", default=[], help="Additional flag to append verbatim.")
    args = parser.parse_args()

    shell = CommandSkeleton(
        action=args.action,
        rl_library=args.rl_library,
        task=args.task,
        preset_tokens=list(args.preset),
        flags=list(args.flag),
    )

    report = {
        "library": LIBRARY_EXTRAS[args.rl_library],
        "common_flags": COMMON_FLAGS,
        "skeleton": shell.to_dict(),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
