---
name: reinforce_training_loop
description: Run bounded REINFORCE stochastic-policy training loops with sampled actions, scalar rewards, baselines, and optimizer traces.
---

# REINFORCE Training Loop

Use this skill to recover or test Williams-style REINFORCE behavior on a small stochastic environment. It is appropriate when the evidence must show sampled stochastic actions, scalar reinforcement, score-function updates, and changed policy parameters. Do not use it for deterministic policy-gradient, Q-learning, or supervised imitation-only experiments.

## Inputs

- Initial Bernoulli logit or equivalent stochastic policy parameters.
- Reward function mapping sampled actions to scalar rewards.
- Episode count, learning rate, random seed, and baseline value.
- Optional path to the `score_function_estimator` script for cross-checking the local score term.

## Outputs

- Episode-level trace containing action probability, sampled action, reward, advantage, update, and parameter value.
- Summary metrics before and after training.
- `params_before` and `params_after` fields suitable for Distiller recovery validation.
- Mechanism booleans for stochastic sampling and optimizer execution.

## Workflow

1. Initialize the stochastic policy and compute its expected reward before training.
2. For every episode, sample an action from the current policy distribution.
3. Observe scalar reward and compute the REINFORCE score-function update.
4. Apply `theta += learning_rate * update` and record the parameter transition.
5. Report expected reward after training and verify that parameters changed.
6. When used in recovery, save the trace under `recovery/logs/training_trace.json`.

## Validation

Run:

```bash
python scripts/train_bandit.py --episodes 128 --seed 7 --output /tmp/reinforce_trace.json
python -m pytest tests
```

The tests assert that the better action's probability and expected reward improve in a deterministic seeded two-action bandit.

## Limitations

This skill is a reduced mechanism-faithful recovery harness. It does not claim to reproduce every historical example from the paper or delayed-reinforcement variants.
