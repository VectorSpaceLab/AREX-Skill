---
name: batched_environment_layout
description: Build and validate independent batched robotics environments for Isaac Gym style reduced recovery experiments.
---

# Batched Environment Layout

Use this skill when a recovery or benchmark needs to represent many independent simulation environments as one batched state layout. It is appropriate for Isaac Gym style mechanisms where environment instances are duplicated and stepped together. Do not use it to claim real GPU simulation unless the runtime handoff proves an actual GPU physics stack is available.

## Inputs
- `env_count`: positive integer number of environments.
- `state_keys`: ordered state component names such as position and velocity.
- Optional per-environment reset mask.

## Outputs
- A layout dictionary containing `env_count`, `state_keys`, `states`, and `isolation_ok`.
- Reset/update helpers that only affect selected environment indices.

## Workflow
1. Create one list per state key with one value per environment.
2. Validate that every state buffer has exactly `env_count` entries.
3. Apply reset masks by index, never by global overwrite.
4. Use the layout as the input contract for a parallel step pipeline.

## Validation
Run `python tests/test_batch_layout.py` or validate this skill tree with `validate_skill_tree.py --run-tests`.

## Limitations
This skill models the layout and isolation semantics only. It does not implement PhysX, CUDA, or real tensor memory aliasing.
