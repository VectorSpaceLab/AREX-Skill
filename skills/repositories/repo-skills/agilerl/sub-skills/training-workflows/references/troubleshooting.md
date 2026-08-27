# Classical Training Troubleshooting

## Environment And Vectorization

- If vectorized Gymnasium environments fail under multiprocessing, move training code into a function and call it under `if __name__ == "__main__":`.
- If an environment is missing, install the specific Gymnasium extra or choose a simpler smoke environment such as `CartPole-v1`.
- If rendering fails, disable rendering for training smoke checks; pygame/SDL/display dependencies are not required for non-rendered training.

## Algorithm And Space Mismatch

| Symptom | Likely issue | Recovery |
| --- | --- | --- |
| DQN/Rainbow rejects the action space | DQN family expects discrete actions | Use a discrete env or switch to TD3/DDPG/PPO for continuous actions. |
| TD3/DDPG outputs invalid actions | Continuous bounds/config mismatch | Check `action_space`, actor output activation, and action scaling. |
| PPO batch/rollout error | On-policy rollout shape or `num_envs` mismatch | Start with one env, then increase `num_envs` after shape validation. |
| Replay buffer sample error | Missing fields or wrong vector dimension | Store `Transition(...).to_tensordict()` with expected fields and batch size. |

## Config Mistakes

- `INIT_HP` keys are not interchangeable across algorithms.
- `POP_SIZE` should match `population_size` and tournament population size.
- `LEARN_STEP`, `BATCH_SIZE`, and replay capacity must be sensible relative to `num_envs` and `max_steps`.
- `CHANNELS_LAST` must match image observation layout.

## Logging And Long Runs

- Set W&B/logging off for smoke tests unless credentials are configured.
- Start with tiny `max_steps`, `evo_steps`, and `eval_loop` values for checks.
- Confirm CUDA availability before assuming GPU acceleration.
