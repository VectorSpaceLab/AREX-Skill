---
name: goal_effect_induction
description: Induce separated goal and effect rules from behavioral cloning traces while logging training evidence.
---

# goal_effect_induction

Use this skill when recovering Bain and Sammut style behavioural cloning without the original simulator repository. It is not a general reinforcement-learning skill; it targets trace-driven reactive cloning with explicit GRAIL-style separation.

## Inputs
- JSON-compatible trace examples or prepared examples, depending on the script.
- Current-attempt artifacts only; do not read any original source repository.

## Outputs
- Deterministic JSON-compatible structures that can be consumed by downstream recovery modules.

## Workflow
1. Induce threshold goal rules from state variables.
2. Induce effect rules that map goal error to elevator actions.
3. Optionally run a tiny scalar optimizer step for reduced recovery evidence.

## Validation
Run `python scripts/goal_effect_induction.py --help` where applicable and run the tests through the Distiller skill-tree validator with `--run-tests`.

## Limitations
The scripts implement a reduced proxy for the paper mechanism. They validate trace preparation, GRAIL separation, compactness, and reactive action prediction; they do not recreate the unavailable flight simulator.
