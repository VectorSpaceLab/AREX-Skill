---
name: reactive_controller_evaluation
description: Evaluate GRAIL-style reactive behavioral clones with metrics, predictions, and mechanism checks.
---

# reactive_controller_evaluation

Use this skill when recovering Bain and Sammut style behavioural cloning without the original simulator repository. It is not a general reinforcement-learning skill; it targets trace-driven reactive cloning with explicit GRAIL-style separation.

## Inputs
- JSON-compatible trace examples or prepared examples, depending on the script.
- Current-attempt artifacts only; do not read any original source repository.

## Outputs
- Deterministic JSON-compatible structures that can be consumed by downstream recovery modules.

## Workflow
1. Run the separated goal/effect controller on held-out examples.
2. Compare against a direct cloning baseline.
3. Emit numeric metrics and mechanism checks for recovery validation.

## Validation
Run `python scripts/reactive_controller_evaluation.py --help` where applicable and run the tests through the Distiller skill-tree validator with `--run-tests`.

## Limitations
The scripts implement a reduced proxy for the paper mechanism. They validate trace preparation, GRAIL separation, compactness, and reactive action prediction; they do not recreate the unavailable flight simulator.
