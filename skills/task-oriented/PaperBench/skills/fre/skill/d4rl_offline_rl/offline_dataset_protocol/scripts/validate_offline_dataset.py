#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_KEYS = {"observation", "action", "reward", "next_observation", "terminal", "timeout"}


def load_dataset(path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data, {}
    if isinstance(data, dict):
        transitions = data.get("transitions", [])
        metadata = {key: value for key, value in data.items() if key != "transitions"}
        return transitions, metadata
    return [], {"format_error": "dataset must be a list or object"}


def validate_dataset(transitions: Any, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = metadata or {}
    errors: list[str] = []
    terminal_count = 0
    timeout_count = 0
    rewards: list[float] = []

    if not isinstance(transitions, list) or not transitions:
        errors.append("transitions must be a non-empty list")
        transitions = []

    for index, transition in enumerate(transitions):
        if not isinstance(transition, dict):
            errors.append(f"transition {index} is not an object")
            continue
        missing = sorted(REQUIRED_KEYS - set(transition))
        if missing:
            errors.append(f"transition {index} missing keys: {', '.join(missing)}")
            continue
        try:
            rewards.append(float(transition["reward"]))
        except Exception:
            errors.append(f"transition {index} reward is not numeric")
        if bool(transition["terminal"]):
            terminal_count += 1
        if bool(transition["timeout"]):
            timeout_count += 1

    tags = ["fixed_dataset"]
    for key in ["quality_tags", "tags"]:
        value = metadata.get(key)
        if isinstance(value, list):
            tags.extend(str(item) for item in value)
    tags = sorted(set(tags))

    return {
        "ok": not errors,
        "transition_count": len(transitions),
        "terminal_count": terminal_count,
        "timeout_count": timeout_count,
        "episode_end_count": terminal_count + timeout_count,
        "reward_sum": sum(rewards),
        "quality_tags": tags,
        "metadata": metadata,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_json")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    transitions, metadata = load_dataset(args.dataset_json)
    report = validate_dataset(transitions, metadata)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
