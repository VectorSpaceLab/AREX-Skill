---
name: go_explore_robustification_evaluation
description: Evaluate Go-Explore archived trajectories with deterministic replay and bounded perturbation checks for recovery evidence.
---

# Go-Explore Robustification Evaluation

Use this skill after a Go-Explore Phase 1 archive has produced one or more promising trajectories. It separates discovery from evaluation by replaying the discovered trajectory and reporting numeric success metrics. In bounded recovery, it provides a reduced proxy for the paper's robustification phase.

## Inputs

- Best archived trajectory with action list and target score.
- Environment factory or compatible step function.
- Perturbation policy or deterministic replay setting.

## Outputs

- Success rate, score, and replay trace.
- Mechanism checks identifying whether this is full robustification or a reduced proxy.
- Validator-ready metric fields for recovery artifacts.

## Workflow

1. Replay the archived trajectory in a fresh environment from the start state.
2. Confirm that the replay reaches the expected goal or score.
3. Optionally run bounded perturbation checks by starting from nearby curriculum points or injecting no-op perturbations.
4. Report numeric metrics and declare reduced/proxy status when no neural policy is trained.

## Validation

Run `python tests/test_robustification.py` or validate with `validate_skill_tree.py --run-tests`.

## Limitations

This skill does not claim to reproduce the paper's multi-day neural robustification. It creates auditable reduced evidence that discovery and robustness checks are distinct.

Refinement cycle 3 note: bounded perturbation replay must be logged separately from deterministic replay; success rate is treated as proxy evidence, not full robustification.
