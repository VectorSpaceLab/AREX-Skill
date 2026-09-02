---
name: successor_feature_model
description: Compute and validate successor-feature reward decompositions for shared-dynamics reinforcement-learning tasks with changing linear rewards.
---

# Successor Feature Reward Decomposition

Use this skill when an RL task family shares transition dynamics but changes rewards through a linear feature-weight vector. Do not use it for tasks where rewards cannot be represented or approximated as `phi(s,a,s')^T w`.

## Inputs

- Finite states and actions.
- Deterministic or stochastic transition entries with transition feature vectors.
- A fixed deterministic policy or action-probability table.
- Discount factor `gamma`.
- Optional reward weight vectors for value reweighting.

## Outputs

- Successor-feature table `psi[state][action][feature]`.
- Dot-product action values for each supplied reward vector.
- Bellman residual and iteration diagnostics.

## Workflow

1. Normalize transitions into expected feature and next-state probabilities.
2. For each policy, solve `psi(s,a) = E[phi(s,a,s') + gamma psi(s', pi(s'))]` by bounded value iteration.
3. Keep reward weights out of the successor-feature update.
4. Convert successor features to task values only through `psi^T w`.
5. Reject shape mismatches, missing state-action pairs, and non-convergent updates unless explicitly running a diagnostic.

## Validation

Run:

```bash
python scripts/successor_features.py --self-test
python tests/test_successor_features.py
```

## Limitations

This skill is intended for small finite recovery experiments or as an exact reference implementation. Large continuous tasks require function approximation not implemented here.
