from __future__ import annotations

import argparse
import json
from pathlib import Path

HUNGER_RANK = {"satiated": 0, "not_hungry": 1, "hungry": 2, "weak": 3, "fainting": 4}


def recommend_survival_action(memory: dict, fresh_age_limit: int = 50, prayer_cooldown: int = 500) -> dict:
    hero = memory.get("hero", {})
    hunger = str(hero.get("hunger", "unknown"))
    turn = int(hero.get("turn", memory.get("turn", 0)) or 0)
    corpses = memory.get("corpses", [])
    for corpse in corpses:
        if corpse.get("safe") is True and int(corpse.get("age", fresh_age_limit + 1)) <= fresh_age_limit and hunger != "satiated":
            return {"action": "eat_corpse", "target": corpse.get("name", "corpse"), "rule": "fresh_safe_corpse", "actions": ["eat", corpse.get("inventory_letter", "ground")]} 
    inventory = memory.get("inventory", [])
    foods = [item for item in inventory if item.get("category") == "food"]
    if HUNGER_RANK.get(hunger, -1) >= HUNGER_RANK["hungry"] and foods:
        item = foods[0]
        return {"action": "eat_inventory_food", "target": item.get("name", "food"), "rule": "inventory_food_when_hungry", "actions": ["eat", item.get("letter", "?")]} 
    last_prayer = int(hero.get("last_prayer_turn", -10**9) or -10**9)
    if hunger == "fainting" and turn - last_prayer >= prayer_cooldown:
        return {"action": "pray", "target": "self", "rule": "fainting_prayer_cooldown_elapsed", "actions": ["pray"]}
    return {"action": "none", "target": null_value(), "rule": "no_survival_intervention", "actions": []}


def null_value():
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply AutoAscend-style survival resource rules.")
    parser.add_argument("memory")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    memory = json.loads(Path(args.memory).read_text(encoding="utf-8"))
    result = recommend_survival_action(memory)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
