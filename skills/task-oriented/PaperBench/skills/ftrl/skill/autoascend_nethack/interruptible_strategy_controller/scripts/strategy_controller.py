from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_STRATEGIES = [
    {"name": "emergency_healing", "priority": 100, "requires": ["low_hp"], "actions": ["quaff_healing_or_pray"]},
    {"name": "combat", "priority": 80, "requires": ["hostile_monster_visible"], "actions": ["score_combat_actions"]},
    {"name": "nutrition", "priority": 70, "requires": ["hungry_or_worse"], "actions": ["apply_survival_rules"]},
    {"name": "exploration", "priority": 10, "requires": [], "actions": ["move_to_unexplored_tile"]},
]


def predicate_active(strategy: dict, flags: dict) -> bool:
    return all(flags.get(name) is True for name in strategy.get("requires", []))


def select_strategy(memory: dict, strategies: list[dict] | None = None, previous: str | None = None) -> dict:
    flags = memory.get("derived_flags", {})
    active = [s for s in (strategies or DEFAULT_STRATEGIES) if predicate_active(s, flags)]
    if not active:
        active = [{"name": "wait", "priority": 0, "actions": ["wait"], "requires": []}]
    active.sort(key=lambda item: (-int(item.get("priority", 0)), str(item.get("name", ""))))
    selected = active[0]
    interrupted = previous is not None and previous != selected["name"]
    reason = "higher_priority_active" if interrupted else "selected_active_strategy"
    return {
        "selected_strategy": selected["name"],
        "interrupted": interrupted,
        "interruption_reason": reason,
        "actions": list(selected.get("actions", [])),
        "active_strategies": [s["name"] for s in active],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Select an interruptible AutoAscend-style strategy.")
    parser.add_argument("memory")
    parser.add_argument("--previous", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    memory = json.loads(Path(args.memory).read_text(encoding="utf-8"))
    result = select_strategy(memory, previous=args.previous or None)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
