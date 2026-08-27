# PPO Core API Reference

This page records the shared PPO implementation used by the repository's training, evaluation, and visualization routes.

## Source of truth

Verified from `PPO.py` source inspection and live import/signature checks:

- `ActorCritic` signature: `(state_dim, action_dim, has_continuous_action_space, action_std_init)`
- `PPO` signature: `(state_dim, action_dim, lr_actor, lr_critic, gamma, K_epochs, eps_clip, has_continuous_action_space, action_std_init=0.6)`
- `RolloutBuffer.clear()` empties the stored lists in place.

## Device behavior

The shared PPO module selects CUDA when `torch.cuda.is_available()` is true and falls back to CPU otherwise. The original repository code also clears CUDA cache on import.

## Objects and methods

### `RolloutBuffer`

Stores the on-policy rollout used by PPO updates:

- `actions`
- `states`
- `logprobs`
- `rewards`
- `state_values`
- `is_terminals`

`clear()` removes all collected items so the next rollout starts empty.

### `ActorCritic`

Two hidden layers of width 64 drive both actor and critic heads.

- Continuous policies use `MultivariateNormal` with a diagonal covariance matrix.
- Discrete policies use `Categorical` with a softmax actor head.
- `set_action_std(new_action_std)` updates the continuous-action variance.
- `act(state)` samples an action, returns the action, its log-probability, and the state value.
- `evaluate(state, action)` returns log-probabilities, state values, and entropy for PPO updates.

### `PPO`

Owns the rollout buffer, current policy, frozen policy copy, and Adam optimizer.

- `set_action_std(new_action_std)` updates both policy copies for continuous action spaces.
- `decay_action_std(action_std_decay_rate, min_action_std)` linearly decays the continuous policy exploration scale.
- `select_action(state)` stores the rollout tuple and returns an action.
  - Continuous actions are returned as a flattened NumPy array.
  - Discrete actions are returned as a Python `int`.
- `update()`
  - computes Monte Carlo returns,
  - normalizes rewards,
  - computes advantages,
  - runs PPO clipped-surrogate optimization for `K_epochs`,
  - copies the updated weights back to `policy_old`,
  - clears the rollout buffer.
- `save(checkpoint_path)` writes `policy_old.state_dict()` with `torch.save`.
- `load(checkpoint_path)` loads the saved state dict into both `policy_old` and `policy`.

## Behavioral notes

- The checkpoint stores model weights only, not optimizer state, buffer contents, environment metadata, or continuous `action_std`.
- Continuous policies need the same `action_std_init` assumption used when the checkpoint was trained or saved.
- The evaluation and training routes use the same constructor shape, so state/action dimensions must match the live environment.

## When to read this file

Read this file when you need exact signatures, action-selection behavior, save/load semantics, or a quick reminder of how PPO updates are structured in this repository.
