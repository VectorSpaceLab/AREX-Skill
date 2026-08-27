# RL Reference

## Verified helpers

- `discount_episode_rewards(rewards=None, gamma=0.99, mode=0)`
- `choice_action_by_probs(probs=(0.5, 0.5), action_list=None)`
- `discount_rewards`

## Evidence summary

This page distills TensorLayer's RL helper module and tutorial README into lightweight utility guidance. Full Q-learning and DQN examples are treated as dependency-heavy reference workflows.

## Practical notes

- The helper functions are lightweight and can be exercised on tiny synthetic inputs.
- The tutorial scripts are reference-first because they depend on Gym, long episode loops, and optional plotting or checkpoint files.
- `discount_episode_rewards` has different modes for resetting across non-zero rewards.
- `choice_action_by_probs` is stochastic unless the probability vector contains a deterministic 1.0 entry.
