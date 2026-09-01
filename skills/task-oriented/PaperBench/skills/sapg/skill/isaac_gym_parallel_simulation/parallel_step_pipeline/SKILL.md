---
name: parallel_step_pipeline
description: Execute a deterministic batched simulation policy reward reset loop for Isaac Gym mechanism recovery.
---

# Parallel Step Pipeline

Use this skill to run a small executable proxy for Isaac Gym's end-to-end loop: read state buffers, compute observations and actions, step all environments, compute rewards, and reset completed environments. It is meant for recovery harnesses and stress tests when the real Isaac Gym GPU runtime is blocked.

## Inputs
- A batched layout with `position` and `velocity` arrays.
- A policy gain or callable action rule.
- Step count and reset threshold.

## Outputs
- Final states, reward totals, reset count, operation count, and a deterministic mechanism report.

## Workflow
1. Validate the layout has the required state arrays.
2. Compute actions from current positions in one batched loop.
3. Update velocity and position arrays without cross-environment writes.
4. Compute rewards and reset only environments crossing the threshold.
5. Compare against a sequential reference when required.

## Validation
Run `python tests/test_parallel_pipeline.py` or validate this skill tree with tests enabled.

## Limitations
The implementation is a CPU standard-library proxy. It preserves control/data-flow semantics but not PhysX contact dynamics.
