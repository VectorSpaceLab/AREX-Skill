---
name: usfa_policy_conditioning
description: Represent USFA policies with reward-weight encodings z and compute greedy policy actions under those encodings.
---

# USFA Policy Conditioning

Use this skill when a USFA recovery needs to condition successor-feature predictions on a policy encoding `z`. Do not use it to evaluate a target task over multiple candidates; the GPI skill owns that aggregation.

## Inputs

- Candidate policy encodings `z`.
- A successor-feature table keyed by state, action, and encoding.
- Action set and state.

## Outputs

- Canonical candidate encodings.
- `psi(s,a,z)` lookups.
- Greedy action under an encoded policy: `argmax_a psi(s,a,z)^T z`.

## Workflow

1. Build a deterministic candidate set from training, target, or sampled encodings.
2. Preserve each encoding as the policy identifier.
3. For Bellman bootstrapping, score each action with the same encoding `z`.
4. Return the greedy action and score table for audit logs.

## Validation

Run:

```bash
python tests/test_policy_conditioning.py
```

## Limitations

This skill assumes tabular or already-computed successor features. It does not train neural USFA approximators.
