---
name: interruptible_strategy_controller
description: Select and interrupt prioritized symbolic NetHack strategies with explicit action queues.
---
# Interruptible Strategy Controller

Use this skill when a symbolic NetHack agent must choose among non-atomic strategies such as exploration, combat, healing, or survival. Do not use it for combat scoring details; pass combat states to a scorer skill after strategy selection.

## Inputs
- State memory with derived flags from the state-memory skill.
- Candidate strategies containing `name`, `priority`, `predicate`, and `actions`.
- Optional previous strategy name.

## Outputs
- Selected strategy name, whether an interruption occurred, interruption reason, and explicit action queue.

## Workflow
1. Evaluate simple predicates against state flags.
2. Sort active strategies by descending priority and stable name.
3. Detect when the selected active strategy differs from the previous strategy.
4. Preserve contextual action wrappers as structured tokens, never ambiguous single keystrokes.
5. Return a safe wait action if no strategy is active.

## Validation
Run `python tests/test_controller.py` or validate the tree with `--run-tests`.

## Limitations
Predicates are deliberately simple for bounded recovery. The skill preserves AutoAscend's interruptible arbitration mechanism rather than full game play.
