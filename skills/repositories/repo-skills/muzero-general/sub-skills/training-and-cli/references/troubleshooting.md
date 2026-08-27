# Training and CLI Troubleshooting

## Invalid game name

Symptom:

```text
<name> is not a supported game name, try "cartpole" ...
ModuleNotFoundError
```

Likely causes:

- The CLI/API game name does not match a module under `games/`.
- The game module exists but imports an optional dependency that is not installed.
- A custom game module is not importable from the bundled source or the staged source root.

Recovery:

1. Run `../games-and-configs/scripts/list_builtin_games.py` to inspect bundled built-ins.
2. For custom modules, stage the bundled source with root `scripts/stage_muzero_source.py --dest <workdir>/muzero-general-source`, add `games/<name>.py`, then run `../games-and-configs/scripts/validate_game_module.py --repo-root <workdir>/muzero-general-source --module games.<name>`.
3. If the module is optional (`lunarlander`, `atari`, `breakout`, `gridworld`, `spiel`), install only its specific dependency after user approval.

## Unknown JSON config key

Symptom:

```text
AttributeError: <game> config has no attribute '<param>'
```

Likely cause: JSON override contains a typo or a field owned by another game/config.

Recovery:

- Read `../games-and-configs/references/configuration-reference.md`.
- Inspect the selected game's `MuZeroConfig` fields with the game listing/validation scripts.
- Use a small known-good override first, for example `{"training_steps": 0, "num_simulations": 1}`.

## GPU conflict with `max_num_gpus = 0`

Symptom:

```text
ValueError: Inconsistent MuZeroConfig: max_num_gpus = 0 but GPU requested by selfplay_on_gpu or train_on_gpu or reanalyse_on_gpu.
```

Recovery:

- For CPU runs, set all GPU flags false:

  ```json
  {"max_num_gpus": 0, "train_on_gpu": false, "selfplay_on_gpu": false, "reanalyse_on_gpu": false}
  ```

- For GPU runs, set `max_num_gpus` to `null`/omit it or a positive number, and verify CUDA PyTorch/Ray GPU visibility. GPU training is optional in this skill's minimum verification.

## Ray startup, object store, or stale worker issues

Symptoms:

- Ray reports address/port binding warnings.
- A previous run leaves workers alive.
- Remote task serialization fails with `pkg_resources` or dependency errors.
- The process appears stuck before training output.

Recovery:

1. Use `sub-skills/training-and-cli/scripts/muzero_cli_smoke.py` first; it constructs `MuZero` from bundled `runtime/source/` and shuts Ray down.
2. In custom scripts, call `ray.shutdown()` at the end.
3. If Ray complains about `/dev/shm` or object-store memory, reduce worker count and training scale, or configure Ray outside this skill with user approval.
4. Treat notebook/Colab Ray address warnings as known operational noise only if training continues.
5. If dependency serialization fails, run the root environment checker and `python -m pip check` in the target environment.

## Training runs too long or writes unexpected results

Symptoms:

- The process runs much longer than expected.
- `results/<game>/<timestamp>/` is created unexpectedly.
- Checkpoints/replay buffers are written while only a smoke was intended.

Recovery:

- Set `training_steps` to `0` or a tiny value for smoke.
- Set `save_model` to `false` and call `train(log_in_tensorboard=False)` only when intentionally training.
- Reduce `num_simulations`, `max_moves`, `num_workers`, `batch_size`, and game complexity for bounded experiments.
- Do not use the upstream 7,500-step CartPole CI recipe as a routine smoke.

## TensorBoard shows no data

Likely causes:

- `log_in_tensorboard=False` was used.
- `save_model`/logging did not create `results_path`.
- TensorBoard is pointed at the wrong `results` directory.
- Training ended before `logging_loop` wrote scalars.

Recovery:

- For real monitored training, prefer `scripts/run_muzero.py --mode train --log-in-tensorboard --results-path <results-dir>` and run `tensorboard --logdir <results-dir>`.
- For smoke runs, absence of TensorBoard data is expected.

## Rendering or human opponent blocks automation

Symptoms: process waits at `Press enter to take a step`, asks for rows/columns/actions, or opens a window.

Recovery:

- Use `render=False` in `MuZero.test`.
- Avoid `opponent="human"` in unattended runs.
- Do not call game `render()` methods during smoke checks; use validation scripts instead.

## Gym/Ray deprecation warnings

The repository uses legacy Gym APIs and Ray APIs. Warnings about Gym being unmaintained, `env.seed`, or `pkg_resources` deprecation do not by themselves prove failure. Record them, but judge success by imports, constructor smoke, game contract checks, and explicit exit status.
