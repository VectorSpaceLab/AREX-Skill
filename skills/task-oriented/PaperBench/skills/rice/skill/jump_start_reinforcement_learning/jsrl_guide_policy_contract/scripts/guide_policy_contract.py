#!/usr/bin/env python3
"""Guide-policy validation helpers for reduced JSRL experiments."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Callable


Action = int
Policy = Callable[[int], Action]


@dataclass
class ChainProbe:
    length: int = 7
    start: int = 0
    goal: int = 6
    horizon: int = 6

    @property
    def legal_actions(self) -> tuple[int, int]:
        return (-1, 1)

    def step(self, state: int, action: int) -> tuple[int, float, bool]:
        if action not in self.legal_actions:
            raise ValueError(f"invalid action: {action}")
        next_state = max(0, min(self.goal, state + action))
        done = next_state >= self.goal
        reward = 1.0 if done else 0.0
        return next_state, reward, done

    def progress(self, state: int) -> int:
        return self.goal - state


def right_guide(state: int) -> int:
    return 1


def stationary_or_bad_guide(state: int) -> int:
    return -1


def rollout_progress(policy: Policy, probe: ChainProbe | None = None) -> dict:
    probe = probe or ChainProbe()
    state = probe.start
    start_distance = probe.progress(state)
    actions: list[int] = []
    total_reward = 0.0
    for _ in range(probe.horizon):
        action = int(policy(state))
        if action not in probe.legal_actions:
            return {"valid_actions": False, "useful": False, "error": f"invalid action {action}"}
        state, reward, done = probe.step(state, action)
        actions.append(action)
        total_reward += reward
        if done:
            break
    end_distance = probe.progress(state)
    progress_gain = start_distance - end_distance
    return {
        "valid_actions": True,
        "actions": actions,
        "final_state": state,
        "total_reward": total_reward,
        "progress_gain": progress_gain,
        "success": state >= probe.goal,
        "useful": progress_gain > 0 and total_reward >= 1.0,
    }


def compare_to_baseline(guide: Policy, baseline: Policy | None = None, probe: ChainProbe | None = None) -> dict:
    probe = probe or ChainProbe()
    baseline = baseline or stationary_or_bad_guide
    guide_report = rollout_progress(guide, probe)
    baseline_report = rollout_progress(baseline, probe)
    useful = bool(guide_report.get("valid_actions")) and (
        float(guide_report.get("progress_gain", 0.0)) > float(baseline_report.get("progress_gain", 0.0))
    )
    if guide_report.get("success") and not baseline_report.get("success"):
        useful = True
    return {"guide": guide_report, "baseline": baseline_report, "useful": useful}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    report = compare_to_baseline(right_guide)
    print(json.dumps(report, indent=2))
    return 0 if report["useful"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
