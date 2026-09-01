---
name: jsrl_guide_policy_contract
description: Validate a Jump-Start Reinforcement Learning guide-policy interface and better-than-random progress assumptions before using it for roll-in.
---

# JSRL Guide Policy Contract

## When To Use

Use this skill when a recovery or implementation needs to decide whether a prior policy is suitable as the fixed JSRL guide-policy. It is appropriate for scripted, imitation-trained, offline-RL, or manually engineered guides. Do not use it to train the guide; it only wraps and validates one.

## Inputs

- A callable or table-like guide-policy that maps observations/states to actions.
- An environment or small deterministic probe exposing legal actions and progress-to-goal information.
- Optional baseline/random policy for comparison.

## Outputs

- Validated action selections from `act`.
- A guide quality report with success count, average progress, and `useful: true/false`.
- Warnings for stationary, invalid-action, or adversarial guides.

## Workflow

1. Wrap the guide behind a minimal `act(state)` function.
2. Check every returned action against the environment's legal actions.
3. Run bounded rollouts and compare progress or success against a baseline.
4. Treat a guide as useful only if it improves progress or success enough to create good handoff states.
5. Record limitations when the guide is related-task, stochastic, or suboptimal.

## Validation

Run:

```bash
python scripts/guide_policy_contract.py --demo
python -m pytest tests
```

The script is standard-library only and can also be imported by recovery harnesses.

## Limitations

This skill does not prove the guide is optimal. It only checks the paper's minimum JSRL assumption: the guide can act from observations and is better than a random or stationary baseline on a bounded probe.
