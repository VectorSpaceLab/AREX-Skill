# DQN Troubleshooting

## MountainCar does not learn

Likely causes:

- Exploration rarely reaches the goal before replay fills.
- The chosen Gym version emits a step penalty rather than the terminal-positive
  reward assumed by some repository notes.
- Replay capacity is too large for a short run, so `update()` is never called.
- Reward scaling makes Q-targets and MSE losses very large.

Actions:

1. Confirm whether learning has started by checking `memory_count >= capacity` or
   `memory_counter >= MEMORY_CAPACITY`.
2. Log both raw reward and shaped reward.
3. Try a bounded shaping term such as position progress or a terminal-success
   bonus, then compare against the unshaped run.
4. For smoke tests, lower replay capacity and episode count; for real training,
   keep enough capacity for diverse trajectories.
5. Do not interpret a large `loss/value_loss` alone as failure; the repo README
   notes very large DQN losses can coexist with an improving policy when target
   and online networks diverge during training.

## Replay buffer sampling looks wrong

- Numpy variants store fixed-width rows: `[state, action, reward, next_state]`.
  Check row width is `2 * state_dim + 2`.
- List variants are full-memory trainers: `update()` converts all replay entries
  to tensors and then minibatches. If any list entries are still `None`, the
  memory gate was bypassed.
- The source samples uniformly and does not implement prioritized replay.
- Terminal transitions are not masked in the bootstrap target. If a future agent
  adapts the algorithm for correctness, add `done` to the transition and multiply
  the bootstrap term by `(1 - done)`.

## TensorBoard logs are missing

- The list replay variants log to `./DQN/logs` relative to the current working
  directory.
- No loss scalars appear until the replay buffer is full and `update()` runs.
- Ensure `tensorboardX` imports successfully; the verified stack included it.
- In adapted scripts, prefer a user-provided `--logdir` and call `writer.close()`
  before process exit.
- Launch TensorBoard against the actual run directory, for example
  `tensorboard --logdir DQN/logs` from the directory that contains the generated
  logs.

## Headless render or plotting failures

- `DQN.py`, `naiveDQN.py`, and `DQN_mountain_car_v1.py` call `env.render()` inside
  the training loop and should not be run unchanged on a headless machine.
- Disable render calls for smoke runs, or use a virtual display only when visual
  rendering is explicitly required.
- Plotting variants use Matplotlib interactive calls. For noninteractive runs,
  switch to a non-GUI backend and save plots instead of pausing a live window.
- Prefer the bundled `scripts/dqn_discrete_probe.py` for environment checks; it
  never renders.

## Gym API and legacy env warnings

- The repo code uses old Gym API style: `state = env.reset()`,
  `next_state, reward, done, info = env.step(action)`, and `env.seed(seed)`.
- Newer Gym/Gymnasium APIs may return `(obs, info)` from reset and
  `(obs, reward, terminated, truncated, info)` from step. Add a tiny wrapper if
  adapting the scripts.
- `CartPole-v0` and `MountainCar-v0` were verified with 4-tuple steps in the
  prepared stack, but future environments may emit deprecation warnings.
- The DQN scripts often use `env.unwrapped`, which removes Gym `TimeLimit`
  behavior. Keep the source's inner `t >= 9999` guard or add your own max-step
  limit when adapting.
