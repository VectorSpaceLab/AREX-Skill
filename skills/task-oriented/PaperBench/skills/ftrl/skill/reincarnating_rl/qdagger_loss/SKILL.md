---
name: qdagger_loss
description: Compute the QDagger objective for policy-to-value reincarnating RL using n-step TD loss plus teacher-policy distillation.
---

# QDagger Loss

## When To Use

Use this skill when implementing or validating a reduced or full QDagger-style policy-to-value reincarnating RL experiment. It is appropriate when you have transition records, student Q-values, and teacher action probabilities. Do not use it as a standalone imitation-only objective; the TD and distillation terms must remain separately visible.

## Inputs

- `q_values`: mapping from state ids to action-value lists.
- `transitions`: records with `state`, `action`, `n_step_return`, `discount`, `next_max_q`, and `teacher_policy`.
- `temperature`: positive softmax temperature for deriving the student policy from Q-values.
- `lambda_t`: current distillation coefficient.

## Outputs

- `td_loss`: mean squared Bellman error.
- `distillation_loss`: mean teacher cross-entropy against the student softmax policy.
- `combined_loss`: `td_loss + lambda_t * distillation_loss`.
- `examples`: per-transition targets, predictions, and loss terms.

## Workflow

1. Validate that every transition has a known state, valid action index, and normalized teacher policy.
2. Compute each n-step TD target as `n_step_return + discount * next_max_q`.
3. Compute mean squared TD loss over selected actions.
4. Convert each student Q-vector into `softmax(q / temperature)`.
5. Compute teacher-policy cross-entropy.
6. Return both component losses and the combined QDagger loss.

## Validation

Run:

```bash
python scripts/qdagger_loss.py --self-test
python tests/test_qdagger_loss.py
```

## Limitations

This implementation is deterministic and dependency-free. It is intended for recovery harnesses, tests, and small tabular/scalar checks, not high-throughput deep RL training.
