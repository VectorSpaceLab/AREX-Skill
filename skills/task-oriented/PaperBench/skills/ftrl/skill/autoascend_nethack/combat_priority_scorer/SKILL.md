---
name: combat_priority_scorer
description: Rank simplified AutoAscend combat actions with symbolic safety, damage, and line-of-fire checks.
---

# Combat Priority Scorer

Use this skill when a symbolic NetHack controller needs a deterministic combat-action ranking. It preserves AutoAscend’s paper mechanism: reduce combat to a smaller action set and score actions by safety and tactical value.

## Inputs
- A JSON combat state with `hero` and `monsters` fields.
- Optional candidate actions and weights when importing the script as a helper.

## Outputs
- `selected_action`.
- `ranked_actions`, each with score and reasons.

## Workflow
1. Identify low-HP survival pressure.
2. Identify hostile targets, peaceful blockers, and hazardous monsters.
3. Score defense, melee, ranged, ray, wait, and other supplied actions.
4. Penalize unsafe actions such as meleeing floating eyes or shooting through peaceful monsters.
5. Return a stable ranking and the top action.

## Validation
Run `python scripts/combat_scorer.py state.json --output combat.json` or the tests. The tests verify low-HP healing, floating-eye avoidance, and line-of-fire penalties.

## Limitations
The scorer is a reusable symbolic approximation. It does not calculate full NetHack damage tables or ray-reflection probabilities.
