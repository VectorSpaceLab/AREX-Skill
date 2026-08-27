# Algorithm and Run Guide

## Purpose

Read this for the standard Atari Breakout/Pong DQN and PPO workflow contracts:
command shapes, training constants, checkpoints, W&B logging, Nature CNN models,
DQN replay storage, PPO GAE, and benchmark caveats. Source workflow labels are
`3-atari/1-dqn.py` for DQN and `3-atari/2-ppo.py` for PPO; they are provenance
labels, not dependencies of this reference.

## Command-shape contracts

When operating on a checkout or an equivalent local entrypoint, use these shapes
rather than the bundled smoke helper. Replace `<atari-dqn-entrypoint>` or
`<atari-ppo-entrypoint>` with the user's actual local entrypoint for the
standard Atari workflow.

```bash
# DQN training, local metrics only
python <atari-dqn-entrypoint> --env breakout --device auto
python <atari-dqn-entrypoint> --env pong --device cpu

# DQN checkpoint replay/test; expects atari_dqn.pt in the working directory
python <atari-dqn-entrypoint> --env breakout --test --device auto

# PPO training, local metrics only
python <atari-ppo-entrypoint> --env breakout --device auto
python <atari-ppo-entrypoint> --env pong --device mps

# PPO checkpoint replay/test; expects atari_ppo.pt in the working directory
python <atari-ppo-entrypoint> --env pong --test --device auto

# Optional W&B logging; requires the user to have logged in first
python <atari-ppo-entrypoint> --env breakout --wandb
python <atari-dqn-entrypoint> --env breakout --wandb
```

Do not run the smoke helper as a trainer. It is a synthetic model/replay/GAE
check only.

## Shared observation and action contract

Both algorithms consume 4 stacked grayscale Atari frames with shape `(4, 84,
84)` and dtype `uint8`. The model normalizes inside `forward()` with
`x.float() / 255.0`. The action dimension comes from the ALE action space of the
selected game; do not hard-code a specific Breakout or Pong action count in
training code unless it has just been read from the env.

## DQN workflow

### Key constants

| Constant | Value | Use |
| --- | ---: | --- |
| `SAVE_PATH` | `atari_dqn.pt` | Raw Torch `state_dict` checkpoint written after training and loaded by `--test`. |
| `TOTAL_FRAMES` | `10_000_000` | Laptop-oriented run length; still expensive. |
| `BUFFER_CAPACITY` | `500_000` | Single-frame replay capacity, roughly multi-GB RAM at Atari size. |
| `BATCH_SIZE` | `32` | Replay sample batch. |
| `GAMMA` | `0.99` | Discount. |
| `LR` | `1e-4` | Adam learning rate. |
| `LEARN_START` | `80_000` | Pure exploration frames before gradient updates. |
| `TRAIN_EVERY` | `4` | Train every 4 env frames. |
| `TARGET_UPDATE_EVERY` | `250` | Target-network copy interval in training steps. |
| `EPSILON_START` | `1.0` | Initial exploration. |
| `EPSILON_END` | `0.01` | Final exploration. |
| `EPSILON_DECAY_FRAMES` | `1_000_000` | Linear epsilon decay horizon. |

### Nature CNN Q-network

The DQN model is the standard Nature CNN for stacked Atari frames:

1. `Conv2d(4, 32, kernel_size=8, stride=4)`, ReLU.
2. `Conv2d(32, 64, kernel_size=4, stride=2)`, ReLU.
3. `Conv2d(64, 64, kernel_size=3, stride=1)`, ReLU.
4. Flatten to `64 * 7 * 7`.
5. `Linear(64 * 7 * 7, 512)`, ReLU.
6. `Linear(512, n_actions)` Q-value head.

Inputs are `uint8` frames in `[0, 255]`; normalization happens in `forward()`.
The training loss is Huber/SmoothL1 loss against the one-step target
`reward + (1 - done) * gamma * max_a Q_target(next_state, a)`. Gradients are
clipped to global norm `10.0`.

### Replay buffer behavior

The DQN replay buffer stores only the newest single frame per transition. At
sample time it reconstructs 4-frame stacks, which saves about 4x memory versus
storing full stacks at every slot.

Operational details:

- `push(frame, action, reward, done)` stores a single `84 x 84` `uint8` frame,
  integer action, clipped reward, and terminal flag.
- `sample(batch_size, device)` returns Torch tensors for `states`, `actions`,
  `rewards`, `next_states`, and `dones` on the selected device.
- Sampling before at least `stack + 2` frames exist raises `RuntimeError("buffer
  too small to sample yet")`.
- Reconstructed stacks mask out frames that would cross a previous terminal
  boundary, so post-life-loss states do not include invalid frames from the
  previous life/episode.
- When the circular buffer is full, sample selection rejects indices that would
  straddle the write head and read stale frames.

The training loop clips env rewards with `np.sign(reward)` before storage.
Logged returns still use raw env rewards for per-life and per-game reporting.

## PPO workflow

### Key constants

| Constant | Value | Use |
| --- | ---: | --- |
| `SAVE_PATH` | `atari_ppo.pt` | Raw Torch `state_dict` checkpoint written after training and loaded by `--test`. |
| `TOTAL_FRAMES` | `10_000_000` | Laptop-oriented run length. |
| `N_ENVS` | `8` | Number of synchronous vector envs. |
| `ROLLOUT_STEPS` | `128` | Steps per env per update. |
| `EPOCHS` | `4` | PPO optimization passes per rollout. |
| `MINIBATCH_SIZE` | `256` | PPO minibatch size. |
| `CLIP_COEF` | `0.1` | Policy and value clipping width. |
| `GAMMA` | `0.99` | Discount. |
| `GAE_LAMBDA` | `0.95` | GAE trace parameter. |
| `LR` | `2.5e-4` | Adam learning rate, linearly annealed to 0. |
| `VALUE_COEF` | `0.5` | Value-loss weight. |
| `ENTROPY_COEF` | `0.01` | Entropy bonus weight. |
| `MAX_GRAD_NORM` | `0.5` | Gradient clipping norm. |

### Actor-critic model

PPO uses the same Nature CNN convolutional trunk, but initializes layers
orthogonally and attaches separate heads:

- policy head: `Linear(512, n_actions)` with gain `0.01` to keep the initial
  action distribution close to uniform;
- value head: `Linear(512, 1)` with gain `1.0`.

The forward pass returns `(logits, values)`, where logits are passed to a
categorical distribution and values have shape `(batch,)`.

### Rollout and GAE

PPO collects a rollout array of shape `(ROLLOUT_STEPS, N_ENVS, 4, 84, 84)`. It
stores actions, old log-probabilities, clipped rewards, done flags, and values.
After the rollout, it computes GAE backward:

```text
delta_t = reward_t + gamma * next_value_t * (1 - done_t) - value_t
adv_t   = delta_t + gamma * lambda * (1 - done_t) * adv_{t+1}
return_t = adv_t + value_t
```

A done flag at life loss cuts the GAE trace, matching the life-loss terminal
contract from the preprocessing reference. Advantages are normalized per
minibatch before the clipped-surrogate update.

## W&B logging

W&B is opt-in with `--wandb` only.

- DQN project name: `rl-atari-dqn`.
- PPO project name: `rl-atari-ppo`.
- The user must authenticate with their own W&B account before enabling the
  flag.
- Omit `--wandb` for offline runs, CI, smoke tests, or environments without
  credentials/network.
- Metrics include global step, recent mean per-life return, recent mean
  per-game return when available, and algorithm-specific loss/learning-rate
  values.

## Checkpoints and `--test`

| Workflow | Checkpoint filename | Loader expectation |
| --- | --- | --- |
| DQN | `atari_dqn.pt` | Q-network `state_dict` with the selected env's `n_actions`. |
| PPO | `atari_ppo.pt` | Actor-critic `state_dict` with the selected env's `n_actions`. |

`--test` loads the checkpoint from the current working directory and replays
forever using the workflow's policy. It is not a short evaluation harness by
itself; stop it manually when enough episodes have been observed. In the source
workflow, `--test` requests human rendering, so headless machines need display
setup or a modified local evaluation entrypoint.

## Benchmark caveats

The README's standard Atari benchmark is for Breakout only:

| Algorithm | Run budget and environment | Reported final mean per-game return | Hardware/protocol notes |
| --- | --- | ---: | --- |
| DQN | 10M agent steps, `ALE/Breakout-v5` with sticky actions | `93.5 ± 9.6` over the final 20 games | Single seed; MacBook Pro M3, 8 GB, MPS; about 9h in the documented run. |
| PPO | 10M agent steps, `ALE/Breakout-v5` with sticky actions | `261.9 ± 6.4` over the final 20 games | Single seed; same laptop/protocol; about 3.8h in the documented run. |

Do not present these as paper-level or statistically robust results. Sticky
actions make absolute scores lower than deterministic `*-v4` comparisons often
found in older papers. CPU/GPU percentages and RAM are process-monitoring
observations from one machine, not portable guarantees. Pong shares the same
workflow contract, but the README does not provide a Pong benchmark row.

## Safe validation path

For model/replay/GAE debugging, run:

```bash
python scripts/atari_basic_smoke.py --device cpu
```

The helper checks the same model shapes, replay terminal masking, GAE reset
behavior, and tiny gradient steps using synthetic frames. It deliberately avoids
ROM-dependent env creation and 10M-frame training.
