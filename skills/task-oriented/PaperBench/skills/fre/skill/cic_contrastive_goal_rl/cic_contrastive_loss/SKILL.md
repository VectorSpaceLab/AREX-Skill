---
name: cic_contrastive_loss
description: Compute CIC normalized skill-transition contrastive loss, logits, margins, and tiny dependency-free training updates.
---

# CIC Contrastive Loss

Use this skill when implementing the CIC representation-learning objective from paired transition tuples and continuous skills. It owns the normalized query/key logits, diagonal-positive labels, cross-entropy loss, and reduced optimizer update diagnostics.

## Inputs

- `tau`: transition tuple matrix `[batch, transition_dim]`.
- `skills`: continuous skill matrix `[batch, skill_dim]`.
- `query_weights`: linear weights mapping skills to embedding space.
- `key_weights`: linear weights mapping transitions to embedding space.
- `temperature`: positive scalar.

## Outputs

- `loss`: diagonal-positive cross entropy.
- `logits`: normalized query-key similarity matrix divided by temperature.
- `positive_logit_margin`: mean diagonal logit minus mean off-diagonal logit.
- `training_trace` when running the reduced update helper.

## Workflow

1. Encode skills as queries and transition tuples as keys with linear maps.
2. Normalize each query and key vector to unit length.
3. Compute `query @ key.T / temperature`.
4. Treat diagonal entries as positives and off-diagonal entries as negatives.
5. Compute cross entropy and positive-pair margin.
6. For reduced recovery, run the provided finite-difference gradient step and record parameter changes.

## Validation

Run:

```bash
python scripts/cic_loss.py --demo
python tests/test_cic_loss.py
```

## Limitations

The script is dependency-free and designed for tiny reduced recovery, not efficient full-scale RL training. A production implementation should use an autodiff framework such as PyTorch.
