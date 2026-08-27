# DQN Family Map

This reference distills the repository's Char01 DQN examples into reusable
operating knowledge. File names below are provenance labels from the original
repo; runtime instructions should use the distilled patterns here rather than
linking to or requiring that checkout.

## Variant map

| Variant | Environment | Network | Replay | Update / target copy | Practical use |
| --- | --- | --- | --- | --- | --- |
| `DQN_CartPole-v0.py` | `CartPole-v0`, unwrapped | MLP `num_state -> 100 -> num_action` | Python list of `Transition(state, action, reward, next_state)`, capacity `8000`, batch `256` | Build tensors from full memory; sweep minibatches with `BatchSampler`; hard-copy `target_net <- act_net` every 100 update minibatches | Best reference for CartPole DQN + TensorBoard logging. |
| `DQN_MountainCar-v0.py` | `MountainCar-v0`, unwrapped | Same two-layer MLP as CartPole, with MountainCar dimensions | Same list replay, capacity `8000`, batch `256` | Same update loop and target-copy cadence | Best reference for MountainCar baseline, but default `num_episodes=400000` is intentionally not a smoke. |
| `DQN.py` | `CartPole-v0`, unwrapped | MLP `4 -> 50 -> 30 -> 2` | Numpy ring array with row width `NUM_STATES * 2 + 2`, capacity `2000`, batch `128` | Sample random rows after memory fills; hard-copy target every `Q_NETWORK_ITERATION=100` learn calls | Older CartPole reference; includes custom balance reward shaping plus unconditional render/plot. |
| `DQN_mountain_car_v1.py` | `MountainCar-v0`, unwrapped | MLP `2 -> 30 -> 3` | Numpy ring array with capacity `2000`, batch `32` | Same target-copy-every-100-learns pattern | Older MountainCar reward-scaling/shaping reference; render and plotting are always on. |
| `naiveDQN.py` | `CartPole-v0`, unwrapped | MLP `4 -> 50 -> 30 -> 2` | Numpy ring array with capacity `20000`, batch `128` | Same target-copy-every-100-learns pattern | Negative example: the source comment says the raw-reward version does not work well because the reward is always `1`. |

## CartPole operating notes

- The list-replay CartPole variant sets `seed=1`, `render=False`,
  `num_episodes=2000`, `learning_rate=1e-3`, and `gamma=0.995`.
- Epsilon-greedy action selection is implemented as mostly greedy: choose the
  network argmax, then replace it with a random action when `np.random.rand(1) >=
  0.9`, which is about a 10% random-action rate.
- The older `DQN.py` variant adds a shaped reward based on cart position and pole
  angle:
  `((x_threshold - abs(x))/x_threshold - 0.5) + ((theta_threshold - abs(theta))/theta_threshold - 0.5)`.
- If a user wants a quick CartPole smoke, do not run the full source script.
  Create or adapt a bounded copy with small `num_episodes`, smaller replay
  capacity, `render=False`, and explicit logdir control.

## MountainCar operating notes

- The list-replay MountainCar variant is structurally the same as CartPole but
  uses `MountainCar-v0`, two state dimensions, three actions, and a very large
  episode budget (`400000`).
- The repository README describes MountainCar as sparse/hard and recommends
  adding a reward term positively related to car position. Under many Gym
  versions, including the verified environment, default `MountainCar-v0` rewards
  are step penalties until termination rather than a clean `0/1` terminal signal;
  treat reward shaping as an explicit design choice, not an automatic fact.
- The older `DQN_mountain_car_v1.py` scales rewards as `reward * 100` when the
  reward is positive, otherwise `reward * 5`. This documents the repo author's
  intent to make the rare success signal dominate, but it may not trigger under
  Gym variants that never emit a positive terminal reward.
- More robust shaping options for an adapted script include a small position
  bonus, a velocity/progress term, or terminal-success bonus. Keep the raw env
  reward visible in logs so shaped and unshaped behavior can be compared.

## Replay buffer details

### Numpy ring variants

A transition row is concatenated as:

```text
[state..., action, reward, next_state...]
```

The row width is `NUM_STATES * 2 + 2`. For CartPole this is `10`; for
MountainCar this is `6`. Rows are written at `memory_counter % MEMORY_CAPACITY`.
Learning samples uniformly from the full capacity once `memory_counter >=
MEMORY_CAPACITY`.

### List replay variants

The list variants allocate `[None] * capacity`, overwrite at `memory_count %
capacity`, and update only when the list has been fully populated. At update
time they convert the whole list into tensors, normalize the reward tensor, then
iterate minibatches using `BatchSampler(SubsetRandomSampler(...))`.

### Tuning implications

- If capacity is too large for a smoke run, learning never starts.
- If capacity is too small, samples are highly correlated and overwritten before
  useful exploration occurs.
- `batch_size` must be reasonable relative to capacity; the source uses `256`
  with list replay and `32`/`128` with numpy replay.
- The source targets do not mask terminal transitions in `q_target = reward +
  gamma * max_a Q_target(next_state, a)`. If adapting for correctness, consider
  storing `done` and masking the bootstrap term.

## Target network updates

All DQN variants maintain an online/eval/action network and a target network.
The target network is hard-copied from the online network, not Polyak-averaged.

- List replay variants: copy after every 100 optimizer minibatch updates.
- Numpy ring variants: copy at the start of every 100th `learn()` call.

When tuning instability, check this cadence together with learning rate, reward
scale, and replay capacity. Very large reward scales or position bonuses can
make MSE losses large even when the policy appears to improve.

## TensorBoard logging

The list replay variants use `SummaryWriter('./DQN/logs')` and log:

- `loss/value_loss` during minibatch updates.
- `live/finish_step` at episode end.

Because the logdir is relative, launching from a different working directory
moves the output. In adapted scripts, expose `--logdir` or construct a clear
project-local log directory and close the writer at shutdown.
