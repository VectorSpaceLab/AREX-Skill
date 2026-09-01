---
name: transition_skill_batching
description: Build and validate aligned CIC state-transition and continuous skill batches for contrastive intrinsic control recovery experiments.
---

# Transition Skill Batching

Use this skill when a CIC-style experiment needs to construct `tau = concat(s, s_next)` and preserve alignment between transition tuples and continuous skill vectors. Do not use it for downstream reward evaluation or for contrastive loss computation; those belong to separate skills.

## Inputs

- `states`: two-dimensional numeric rows representing current states.
- `next_states`: two-dimensional numeric rows with the same shape as `states`.
- `skills`: two-dimensional numeric rows with the same batch size.
- Optional synthetic batch arguments: `batch_size`, `state_dim`, `skill_dim`, and `seed`.

## Outputs

- `tau`: transition tuples formed by concatenating each state and next state.
- `metadata`: batch size, dimensions, and source label.
- JSON output when running the CLI script.

## Workflow

1. Validate all arrays are non-empty rectangular numeric matrices.
2. Confirm `states` and `next_states` have identical shapes.
3. Confirm `skills` shares the same batch size.
4. Concatenate current and next states across feature dimension.
5. For reduced recovery, generate a deterministic synthetic batch where each skill controls a repeatable transition direction.

## Validation

Run:

```bash
python scripts/transition_batch.py --demo
python tests/test_transition_batch.py
```

## Limitations

This skill does not estimate rewards, train encoders, or sample from an RL replay buffer. It only preserves the transition-skill data contract needed by CIC.
