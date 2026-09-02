---
name: fb_greedy_policy
description: Extract no-planning greedy policies from FB forward embeddings and a projected reward vector.
---

# FB Greedy Policy Extraction

Use this skill when `z_R` has already been estimated and a policy must be derived by direct FB scoring. Do not use it to plan, search, or update embeddings for the new reward.

## Inputs

- Forward embeddings `F` indexed as state-action rows.
- Task vector `z_R`.
- Number of states and actions, with deterministic row order `state * action_count + action`.

## Outputs

- Q-value table `F(s,a,z_R)^T z_R`.
- Greedy action for each state with deterministic lowest-index tie breaking.

## Workflow

1. Compute dot products for all state-action rows.
2. Group scores by state and select the maximum action.
3. Record ties and avoid any environment planning or reward-specific optimization.
4. Hand the policy to recovery or evaluation modules.

## Validation

Run `python scripts/greedy_policy.py --self-test`. Tests verify known best actions and deterministic tie handling.

## Limitations

The script assumes finite action enumeration and precomputed forward embeddings.
