---
name: survival_resource_rules
description: Apply AutoAscend nutrition and emergency resource rules to symbolic NetHack state memory.
---

# Survival and Resource Rules

Use this skill when hunger, food, corpse, or prayer decisions should preempt ordinary exploration. It is designed for AutoAscend-style symbolic control and bounded recovery tests.

## Inputs
- State memory with `hero.hunger`, `hero.turn`, `hero.last_prayer_turn`, `inventory`, and optional `corpses`.
- Optional rule parameters when importing the helper function.

## Outputs
- Recommended survival action.
- Target item or corpse.
- Rule name and semantic action queue.

## Workflow
1. Prefer fresh safe corpses while the hero is not satiated.
2. If hungry or worse, eat carried food rations or equivalent inventory food.
3. If fainting and prayer cooldown elapsed, pray.
4. Otherwise return an explicit no-action result.

## Validation
Run `python scripts/survival_rules.py memory.json --output survival.json` or the tests. The tests cover safe-corpse preference, ration fallback, prayer cooldown, and no-action cases.

## Limitations
The skill does not identify real NetHack corpse safety from glyphs. Callers must provide safety metadata or combine it with a richer parser.
