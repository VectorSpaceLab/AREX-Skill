from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_ACTIONS = [
    {"name": "heal", "kind": "defense"},
    {"name": "melee_north", "kind": "melee", "target": "nearest"},
    {"name": "ranged_north", "kind": "ranged", "target": "nearest"},
    {"name": "engrave_elbereth", "kind": "defense"},
    {"name": "wait", "kind": "wait"},
]


def score_action(action: dict, state: dict, weights: dict | None = None) -> dict:
    weights = {"damage": 4.0, "survival": 8.0, "risk": -10.0, **(weights or {})}
    hero = state.get("hero", {})
    monsters = state.get("monsters", [])
    hp = float(hero.get("hp", 1) or 1)
    max_hp = float(hero.get("max_hp", 1) or 1)
    low_hp = hp / max(max_hp, 1.0) <= 0.35
    hostile = [m for m in monsters if m.get("hostile") and not m.get("peaceful")]
    peaceful_blocker = any(m.get("peaceful") and m.get("in_line_of_fire") for m in monsters)
    hazardous_adjacent = any(m.get("adjacent") and m.get("name") in {"floating eye", "gas spore"} for m in hostile)
    score = 0.0
    reasons = []
    kind = action.get("kind")
    if kind == "defense" and low_hp:
        score += weights["survival"]
        reasons.append("low_hp_survival_priority")
    if kind in {"melee", "ranged"} and hostile:
        score += weights["damage"]
        reasons.append("hostile_target_available")
    if kind == "melee" and hazardous_adjacent:
        score += weights["risk"]
        reasons.append("hazardous_melee_target")
    if kind in {"ranged", "ray"} and peaceful_blocker:
        score += weights["risk"]
        reasons.append("peaceful_line_of_fire_blocker")
    if kind == "wait":
        score -= 1.0
        reasons.append("low_information_wait")
    return {"action": action.get("name"), "score": score, "reasons": reasons}


def rank_actions(state: dict, actions: list[dict] | None = None, weights: dict | None = None) -> dict:
    ranked = [score_action(action, state, weights) for action in (actions or DEFAULT_ACTIONS)]
    ranked.sort(key=lambda item: (-item["score"], item["action"]))
    return {"selected_action": ranked[0]["action"], "ranked_actions": ranked}


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank AutoAscend-style combat actions.")
    parser.add_argument("state")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    state = json.loads(Path(args.state).read_text(encoding="utf-8"))
    result = rank_actions(state)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
