---
name: linear_reward_successor_features
description: Compute linear multitask rewards, successor-feature values, and vector Bellman targets for USFA-style reinforcement-learning tasks.
---

# Linear Reward Successor Features

Use this skill when a recovery or implementation needs the Universal Successor Features contract `r_w = phi^T w` and `Q = psi^T w`. Do not use it to choose candidate GPI policies; that belongs to the GPI action-selection skill.

## Inputs

- `phi`: transition feature vector.
- `w`: task reward-weight vector.
- `psi`: successor-feature vector for `(state, action, z)`.
- `next_psi`: bootstrap successor-feature vector, or zeros for terminal transitions.
- `gamma`: discount factor.

## Outputs

- Scalar linear reward.
- Scalar Q value.
- Vector Bellman target.
- Vector TD error.

## Workflow

1. Validate equal vector dimensions.
2. Compute `reward = dot(phi, w)`.
3. Compute `q_value = dot(psi, w)`.
4. Compute `target = phi + gamma * next_psi` unless terminal.
5. Compute `td_error = target - psi`.

## Validation

Run:

```bash
python tests/test_successor_features.py
```

## Limitations

This skill assumes observable transition features and linear rewards. It does not learn features from pixels or choose behavior policies.
