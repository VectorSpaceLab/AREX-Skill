# Hyperparameters and source defaults

The values below are the source snapshot's declared defaults. They describe what
is present, not what is safe for a smoke test. A bounded adaptation must state
all overrides explicitly.

## Training constants

| Name | Source value | Role / caution |
|---|---:|---|
| `seed` | `0` | PyTorch and NumPy seeds; Python replay sampler is seeded by the buffer |
| `eval_freq` | `5e3` | Evaluation/checkpoint cadence in environment steps; effectively 5000 |
| `max_ep` | `500` | Maximum environment steps per episode |
| `eval_ep` | `10` | Episodes per evaluation |
| `max_timesteps` | `5e6` | Maximum training steps; not a smoke budget |
| `expl_noise` | `1` | Initial normalized-action Gaussian noise |
| `expl_decay_steps` | `500000` | Linear decay interval |
| `expl_min` | `0.1` | Noise floor |
| `batch_size` | `40` | Caller value passed to `TD3.train`; smaller than method signature default |
| `discount` | `0.99999` | Caller value; unusually close to 1 |
| `tau` | `0.005` | Soft target update coefficient |
| `policy_noise` | `0.2` | Target-policy noise standard deviation |
| `noise_clip` | `0.5` | Target-policy noise clamp |
| `policy_freq` | `2` | Actor/target update cadence within each `train` call |
| `buffer_size` | `1e6` | Maximum replay entries; source passes a float-valued literal, which should be normalized to an integer in portable code |
| `file_name` | `TD3_velodyne` | Checkpoint and evaluation-history stem |
| `save_model` | `True` | Enables checkpoint directory creation and final save |
| `load_model` | `False` | If enabled, source attempts to load online actor/critic |
| `random_near_obstacle` | `True` | Enables held random action branch near obstacles |

The method declaration itself uses `batch_size=100` and `discount=1`; the
training loop explicitly passes the table values. Do not confuse these two
levels when documenting a change.

## Dimensions and action mapping

- `environment_dim=20` and `robot_dim=4`, giving `state_dim=24`.
- `action_dim=2`, `max_action=1`.
- Actor actions are clipped to `[-1, 1]` after exploration noise.
- The first action is converted to `[0, 1]` only at the environment boundary;
  the second remains in `[-1, 1]`.
- The obstacle test examines `state[4:-8]`, i.e. a subset of the laser portion
  rather than the four robot features. If changing state layout, revisit this
  slice instead of assuming it still means the same thing.

## Exploration details

At every step, while `expl_noise > expl_min`, the source subtracts
`(1 - expl_min) / expl_decay_steps`, then adds independent Gaussian noise to
both normalized action components and clips to `[-1, 1]`. Because the decay is
applied before noise generation and has no explicit lower clamp, bounded code
should clamp the noise value to `expl_min` after the decrement.

With `random_near_obstacle=True`, if a uniform draw is greater than `0.85`,
the minimum selected slice of the laser state is below `0.6`, and no held
random action is active, the source chooses a random duration from 8 through 14
(the upper bound is exclusive) and samples a two-component uniform action in
`[-1, 1]`. While active, it decrements the counter, reuses that action, and
forces normalized linear action to `-1`. This is intended to increase
exploration near obstacles, but it mutates the `random_action` array in place;
a robust adaptation can copy it before mutation.

## Episode, training, and evaluation cadence

The outer loop trains once when an episode ends, using that episode's number of
steps as `iterations`. It stores `done_bool=0` on a time-limit termination at
step 500, but sets the loop's `done=1`; actual terminal transitions store
`done_bool=1`. Evaluation occurs after an episode boundary when accumulated
steps since the last evaluation reach `eval_freq`. The source also performs one
final evaluation after the main loop. Checkpoint and `.npy` saves occur at
scheduled evaluations and at the end when saving is enabled.

For smoke tests, reduce all budgets, prefill the replay buffer, and write to a
temporary output root. Do not claim convergence, obstacle avoidance, or
simulator fidelity from a synthetic run.
