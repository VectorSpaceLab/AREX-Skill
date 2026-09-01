---
name: score_function_estimator
description: Compute REINFORCE score-function update terms for sampled stochastic policy actions with scalar rewards and baselines.
---

# Score Function Estimator

Use this skill when a recovery or implementation needs the local REINFORCE likelihood-ratio primitive for a sampled stochastic action. Do not use it for deterministic argmax policies, supervised cross-entropy labels, or value-function-only updates.

## Inputs

- Bernoulli action probability `prob_action_one` in `(0, 1)`.
- Sampled action `0` or `1`.
- Scalar reward or return.
- Optional action-independent baseline.

## Outputs

- `grad_log_prob`: derivative of the sampled action log probability with respect to the Bernoulli logit.
- `advantage`: `reward - baseline`.
- `update`: `advantage * grad_log_prob`.

## Workflow

1. Confirm the action was sampled from the same stochastic policy whose probability is supplied.
2. Clamp the probability only for numerical safety; do not change the action.
3. Compute `grad_log_prob = action - prob_action_one` for a Bernoulli logit policy.
4. Center reinforcement with an action-independent baseline if provided.
5. Return the update direction, leaving learning-rate scaling to the training loop.

## Validation

Run:

```bash
python scripts/score_estimator.py --prob 0.4 --action 1 --reward 1.0 --baseline 0.2
python -m pytest tests
```

The tests verify update signs and that a baseline changes magnitude but preserves the ascent direction in a high-reward action example.

## Limitations

This skill implements the Bernoulli-logit case used by the bounded recovery. Categorical policies use the same score-function principle but require vector log-probability gradients.
