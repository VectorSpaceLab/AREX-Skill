---
name: reduced_fb_recovery
description: Run a bounded soft-mode reduced recovery experiment for forward-backward representations with executable evidence.
---

# Reduced FB Recovery Evaluation

Use this skill when full environment-scale FB training is blocked but soft-mode recovery permits a declared reduced proxy. It coordinates generated FB skills and records evidence that the mechanism ran.

## Inputs

- Paths to generated FB module scripts.
- A runtime handoff showing package/model blockers and allowed sources.
- A small gridworld or transition table for bounded recovery.

## Outputs

- Recovery result JSON with proxy status, metrics, and mechanism checks.
- Command logs, generated-skill invocation logs, generated data item, and training trace.

## Workflow

1. Load runtime handoff and declare whether full neural/environment training is blocked.
2. Execute the occupancy factorization skill on reward-free transitions.
3. Execute reward projection for a late sparse goal.
4. Execute greedy policy extraction and compare actions to shortest-path oracle moves.
5. Record before/after loss, parameter changes, skill invocations, and proxy limitations.

## Validation

Run the recovery harness and then `validate_recovery_experiment.py` on the attempt directory. The experiment is acceptable only when the gate reports `ok: true`.

## Limitations

This is proxy evidence and must not be reported as a full paper-scale reproduction. It is designed to prove mechanism fidelity under bounded runtime constraints.
