# PlaNet Workflows

Use this reference for PlaNet, latent dynamics planning, pixel-control tasks, CEM planning, config presets, task selection, and PlaNet debug runs.

## Family summary

PlaNet learns a compact latent dynamics model from image observations and chooses actions through online planning in latent space. The implementation uses TensorFlow 1-era code and a module CLI.

Primary command recipe:

```bash
python3 -m planet.scripts.train --logdir ./planet-log --params '{tasks: [cheetah_run]}'
```

Debug command recipe:

```bash
python3 -m planet.scripts.train --logdir ./planet-debug --resume_runs False --num_runs 1000 --config debug --params '{tasks: [cheetah_run]}'
```

The debug config reduces episode length, model size, batch shape, collection schedule, and planner work so code paths are easier to exercise. It is not evidence of full training quality.

## Dependency family

The setup evidence lists these core dependencies:

- `tensorflow-gpu==1.13.1`
- `tensorflow_probability==0.6.0`
- `dm_control`
- `gym`
- `matplotlib`
- `ruamel.yaml`
- `scikit-image`
- `scipy`

The README notes Ubuntu 18-era testing and recommends dm_control rendering setup. Treat rendering, MuJoCo, and GPU compatibility as environment prerequisites.

## Train CLI reference

| Flag | Default | Meaning |
|---|---:|---|
| `--logdir` | required | Experiment log root. The training utility creates run subdirectories and episode data under it. |
| `--num_runs` | `1` | Number of run directories to manage. Use large values with `--resume_runs False` for repeatedly starting new debug runs. |
| `--config` | `default` | Configuration function name. Visible options include `default` and `debug`. |
| `--params` | `{}` | YAML-formatted dictionary merged into the config, for example `'{tasks: [cheetah_run]}'`. |
| `--ping_every` | `0` | Conflict-prevention ping interval for multiple workers; `0` disables it. |
| `--resume_runs` | `True` | Boolean parser accepts exactly `True` or `False`. Controls whether unfinished runs are resumed. |

The script parses `--params` with YAML after replacing `#` with `,`, then calls TensorFlow's app runner. Keep shell quoting around the YAML dictionary.

## Task names

The task registry defines these visible task functions:

| Task | Environment family | Default action repeat | Notes |
|---|---|---:|---|
| `dummy` | internal dummy env | `1` | Useful only for code-path testing. |
| `cartpole_balance` | dm_control cartpole/balance | `8` | Pixel observations plus reward/position/velocity diagnostics. |
| `cartpole_swingup` | dm_control cartpole/swingup | `8` | Pixel observations. |
| `finger_spin` | dm_control finger/spin | `2` | Includes touch diagnostics. |
| `cheetah_run` | dm_control cheetah/run | `4` | README's primary example. |
| `cup_catch` | dm_control ball_in_cup/catch | `4` | Pixel observations. |
| `walker_walk` | dm_control walker/walk | `2` | Height/orientation/velocity diagnostics. |
| `reacher_easy` | dm_control reacher/easy | `4` | Includes target diagnostics. |
| `gym_cheetah` | Gym HalfCheetah-v3 | `1` | Source comment says it works with process isolation. |
| `gym_racecar` | Gym CarRacing-v0 | `1` | Source comment says it works with thread isolation. |

For multiple tasks, the config pads actions across task action spaces and keeps reward/state diagnostics aligned.

## Config knobs

### Presets

| Config | Purpose |
|---|---|
| `default` | Full training setup with data processing, model components, tasks, loss functions, and training schedule. |
| `debug` | Overrides defaults with tiny values: fewer seed episodes, short train/test steps, small model/state sizes, small batch shape, frequent collection, and small CEM planner settings. |

### Data processing

Key `--params` keys include:

- `batch_shape`: default `(50, 50)`.
- `num_chunks`: default `1`.
- `image_bits`: default `5`.
- `loader`: one of `cache`, `recent`, `reload`, `dummy`; default `recent`.
- `bound_action`: default `clip`.

### Model components

| Parameter | Default | Meaning |
|---|---:|---|
| `gradient_heads` | `['image', 'reward']` | Prediction heads that receive gradients. |
| `network` | `conv_ha` | Encoder/decoder network module. |
| `activation` | `relu` | Activation key; available keys include `relu`, `elu`, `tanh`, `swish`, `softplus`, `none`. |
| `num_layers` | `3` | Feed-forward head layers. |
| `num_units` | `300` | Feed-forward head width. |
| `model_size` | `200` | Recurrent/dynamics hidden size. |
| `state_size` | `30` | Latent state size. |
| `model` | `rssm` | Latent dynamics model; visible alternatives include `ssm` and `drnn`. |
| `mean_only`, `min_stddev`, `future_rnn`, `model_layers` | varies | Dynamics-model specialization knobs. |

### Loss and schedule

Useful keys include `divergence_scale`, `global_div_scale`, `overshooting_scale`, `overshooting_distance`, `free_nats`, `main_learning_rate`, `main_gradient_clipping`, `train_steps`, `test_steps`, `max_steps`, `checkpoint_every`, `num_seed_episodes`, and collection schedule dictionaries.

### Planning and collection

The visible planner is CEM. Useful `--params` keys include:

| Parameter | Default | Meaning |
|---|---:|---|
| `planner` | `cem` | Planner selector; other values are not implemented in evidence. |
| `planner_amount` | `1000` | Number of action sequences sampled. |
| `planner_iterations` | `10` | CEM iterations. |
| `planner_topk` | `100` | Top candidates kept by CEM. |
| `planner_horizon` | `12` | Planning horizon for collection simulations. |
| `collect_objective` | `reward` | Objective function used by planner. |
| `collect_every` | `5000` | Collection cadence. |
| `train_action_noise` | `0.3` | Exploration noise for training collection. |
| `isolate_envs` | `thread` | Environment isolation; README says some envs work better with `thread`, Gym cheetah notes `process`. |

## Modification guidance

- To add or change tasks, implement a task function that returns the task tuple with name, environment constructor, max length, and state components.
- To change the world model, use `--params '{model: ssm}'` or implement/select another model class with matching config wiring.
- To run ablations from the README: random data collection uses `planner_iterations: 0, train_action_noise: 1.0`; deterministic uses `mean_only: True, divergence_scale: 0.0`; stochastic uses `model: ssm`; one-agent-all-tasks uses `collect_every: 30000`.
- To debug environment isolation failures, switch `isolate_envs` between `thread` and `process` in `--params`.
- Keep `--params` shell quoting valid; malformed YAML is a common cause of early failure.

## Known PlaNet omissions

- No TensorFlow 1.13 runtime, dm_control renderer, MuJoCo, Gym environment, or long training run is verified here.
- `--config debug` is suitable for code-path probing, not for benchmark-quality evidence.
- TensorFlow 1.x GPU dependencies may require an old Python/CUDA stack; resolve environment compatibility before running.
