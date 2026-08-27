# Workflows

## Deterministic reward discount check

1. Build a tiny reward list with a known answer.
2. Call `discount_episode_rewards` with a fixed gamma.
3. Compare the result against the documented example or a manually computed expected vector.

## Deterministic action selection check

1. Use a probability vector with a 1.0 entry.
2. Call `choice_action_by_probs` with a short action list.
3. Confirm the returned action is the one with probability 1.0.

## Full RL tutorial guidance

Treat Q-learning, DQN, and the other tutorial files as reference material unless the user has explicitly asked for the full Gym-based environment and training setup.
