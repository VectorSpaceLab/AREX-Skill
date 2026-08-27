# E2O and PEX offline-to-online workflows

Offline-to-online workflows have two separable responsibilities:

1. Train or locate an offline policy/checkpoint from a fixed dataset.
2. Continue with controlled online interaction using a Gym/D4RL environment and the offline checkpoint when the selected algorithm requires one.

Do not collapse these stages. A future agent should record the offline run name, checkpoint path, environment name, seed, and log directory before building the online command.

## E2O workflow

E2O stands for ensemble-based offline-to-online reinforcement learning. The collection's E2O scripts use a forked d3rlpy-style package named `d3rlpy_new`.

### Offline stage

Recipe shape:

```bash
python offline-rl-algorithms/E2O/E2O-offline.py --dataset halfcheetah-medium-expert-v2 --n_critic 10 --gpu 0 --seed 1
```

Important behavior:

- Loads a D4RL-style dataset via `d3rlpy_new.d3rlpy.datasets.get_dataset`.
- Uses an ensemble CQL-style algorithm configured with `n_critics` from `--n_critic`.
- Uses environment and value-scale scorers during fit.
- Writes d3rlpy log artifacts under the normal d3rlpy logging layout. The online script expects a params JSON and model checkpoint matching the offline run naming convention.

### Online stage

Recipe shape:

```bash
python offline-rl-algorithms/E2O/E2O-online.py --env HalfCheetah-v2 --gpu 0 --seed 1
```

Important behavior:

- Creates Gym train and evaluation environments.
- Loads an `E2O` object from offline `params.json` and model checkpoint files.
- Builds an online replay buffer and calls d3rlpy-style `fit_online`.
- The default script has a hard-coded expectation for the offline run name and checkpoint location. If a task used a different offline dataset, seed, or log location, adapt those values deliberately before online execution.

## Policy Expansion (PEX) workflow

PEX is a separate implementation with offline IQL training and online variants. Use `scripts/build_pex_command.py` for shell-quoted recipes.

### PEX offline stage

Required flags:

- `--env_name`: D4RL/Gym task name, e.g. `antmaze-large-play-v0` or `halfcheetah-random-v2`.
- `--log_dir`: output directory for the offline run. The script refuses to overwrite an existing directory.

Common controls:

- `--seed`, `--discount`, `--hidden_dim`, `--hidden_num`, `--num_steps`, `--batch_size`, `--learning_rate`, `--target_update_rate`, `--tau`, `--beta`, `--eval_period`, `--eval_episode_num`, `--max_episode_steps`.

Recipe shape:

```bash
python offline-rl-algorithms/E2O/PEX-main/main_offline.py --env_name antmaze-large-play-v0 --log_dir runs/antmaze-large-play-v0_offline_run1 --seed 1 --tau 0.9 --beta 10.0 --eval_episode_num 100
```

Offline output:

- The script saves an `offline_ckpt` file in the selected log directory.
- Record that checkpoint path for the online stage.

### PEX online stage

Required flags for this skill's command builder:

- `--algorithm`: one of `scratch`, `buffer`, `direct`, or `pex`.
- `--env_name`: D4RL/Gym task name.
- `--log_dir`: output directory for the online run; the script refuses to overwrite an existing directory.
- `--ckpt_path`: checkpoint path from the offline stage. The implementation strictly asserts a checkpoint for `direct` and `pex`; this sub-skill requires it for all online recipes so handoffs stay explicit.

Common controls:

- `--seed`, `--discount`, `--hidden_dim`, `--hidden_num`, `--batch_size`, `--learning_rate`, `--target_update_rate`, `--tau`, `--beta`, `--replay_size`, `--total_env_steps`, `--initial_collection_steps`, `--updates_per_step`, `--inv_temperature`, `--eval`, `--eval_period`, `--eval_episode_num`, `--max_episode_steps`.

Recipe shape:

```bash
python offline-rl-algorithms/E2O/PEX-main/main_online.py --algorithm pex --env_name antmaze-large-play-v0 --log_dir runs/antmaze-large-play-v0_online_pex_run1 --ckpt_path runs/antmaze-large-play-v0_offline_run1/offline_ckpt --seed 1 --tau 0.9 --beta 10.0 --eval_episode_num 100
```

Algorithm modes:

| Mode | Checkpoint role | Buffer behavior |
| --- | --- | --- |
| `scratch` | Starts online learner without loading an offline checkpoint in the source implementation, but still require explicit user intent. | Single online buffer. |
| `buffer` | Starts without offline network weights in the source implementation. | Double-buffer style sampling from offline dataset plus online memory. |
| `direct` | Loads the offline checkpoint into online IQL. | Double-buffer style. |
| `pex` | Loads the offline checkpoint into the PEX policy expansion algorithm. | Double-buffer style plus inverse-temperature action selection. |

## Practical safeguards

- PEX and E2O runs can create directories, checkpoints, and long training logs. The bundled builders only print commands; they do not create directories or run training.
- The PEX README examples spell the CUDA visibility variable incorrectly in some places. If GPU selection is needed, use the standard CUDA visibility variable name in your shell, not the misspelled variant.
- AntMaze evaluation typically uses more episodes than locomotion tasks. Keep `--eval_episode_num` explicit when comparing runs.
- For online runs, ensure the offline checkpoint is compatible with the exact environment, observation/action dimensions, hidden sizes, tau/beta settings, and policy architecture expected by the online script.
