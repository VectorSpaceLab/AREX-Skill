---
name: mixed_exploration_scheduler
description: Assign mixed Gaussian exploration scales across parallel actors and produce reproducible noisy bounded actions.
---

# Mixed Exploration Scheduler

Use this skill when a PQL or DDPG-style experiment has many parallel actors and should avoid relying on one manually tuned exploration noise scale. It is not needed for algorithms where exploration is entirely defined by a stochastic policy distribution such as standard SAC.

## Inputs

- `actor_count`: positive integer number of actors.
- `scales`: non-empty list of non-negative Gaussian noise scales.
- `base_actions`: deterministic policy actions, either one scalar reused for all actors or one value per actor.
- `low` and `high`: action bounds.
- `seed`: integer random seed for reproducibility.

## Outputs

- Round-robin per-actor scale assignments.
- Noisy clipped action values.
- Diversity statistics such as distinct scales and empirical variance.

## Workflow

1. Validate that the actor count and scale list are usable.
2. Assign scales round-robin so every scale appears when enough actors exist.
3. Use a local random number generator seeded by the caller.
4. Add Gaussian noise to deterministic actions and clip to action bounds.
5. Return assignments and statistics for mechanism checks.

## Validation

Run:

```bash
python scripts/mixed_exploration.py --actor-count 8 --scales 0.2,0.4,0.6,0.8 --base-action 0.0 --seed 7
python tests/test_mixed_exploration.py
```

## Limitations

This skill schedules exploration and creates noisy actions. It does not evaluate whether a particular noise scale is optimal for a real benchmark task.

## Refinement Note

A zero-noise single-scale ablation produces no action diversity; recovery should require at least two distinct nonzero-capable scales when validating mixed exploration.
