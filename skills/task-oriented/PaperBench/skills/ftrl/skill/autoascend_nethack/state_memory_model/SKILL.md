---
name: state_memory_model
description: Build persistent symbolic NetHack state memory from compact observations for AutoAscend-style agents.
---
# Persistent NetHack State Memory

Use this skill when a recovery or agent needs to convert NetHack-like observations into a durable symbolic state. Do not use it to choose actions directly; downstream strategy, combat, and survival modules consume its output.

## Inputs
- Observation dictionaries with `level_id`, `turn`, `hero`, `inventory`, `monsters`, `traps`, `stairs`, `items`, and optional `message` fields.
- Optional previous memory created by this skill.

## Outputs
- JSON-serializable memory with current level, per-level remembered facts, normalized hero and inventory fields, and derived flags.
- Flags include `low_hp`, `hungry_or_worse`, `fainting`, and `hostile_monster_visible`.

## Workflow
1. Load the previous memory if present and preserve facts for non-current levels.
2. Normalize the current observation into stable level facts keyed by coordinate or label.
3. Merge monsters, traps, stairs, and items for the current level.
4. Normalize inventory without inventing unknown item properties.
5. Derive urgent flags that interruptible strategies can inspect.

## Validation
Run `python tests/test_state_memory.py` or the bundled skill validator with `--run-tests`.

## Limitations
This skill handles compact dictionaries, not raw NLE tensors. It preserves paper mechanisms for proxy recovery without requiring the original AutoAscend repository.
