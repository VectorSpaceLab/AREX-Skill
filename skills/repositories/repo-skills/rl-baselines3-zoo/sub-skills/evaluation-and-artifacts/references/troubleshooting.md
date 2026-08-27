# Troubleshooting evaluation and artifacts

Use this reference after checking the local artifact layout. Prefer fixing paths, selectors, or missing local files before changing model code.

## Quick diagnostic order

1. Run the bundled inspector with the same `--folder`, `--algo`, `--env`, `--exp-id`, and selector flags you plan to pass to `enjoy`.
2. If the selected model file is missing, choose another selector or route artifact creation to `training-cli`.
3. If config or normalization files are missing, decide whether the model can be evaluated without those training-time settings.
4. Add `--no-render` for headless sessions.
5. Avoid implicit Hub fallback unless the task explicitly permits network/model download behavior.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No model found for <algo> on <env>, path: <path>` | The resolved selector path does not exist. The folder, algorithm, env id, exp id, or selector is wrong; or training did not save that artifact. | Inspect with `scripts/model_artifact_inspector.py`. For final model use no selector; for best use `--load-best`; for checkpoint use the exact step number or `--load-last-checkpoint`. If no model exists, route to `training-cli`. |
| `The <path> folder was not found` | The run folder computed from `-f/--folder`, `--algo`, `--env`, and `--exp-id` is absent. | Check whether the log root is the parent that contains algorithm folders. Use `--exp-id 1` for `<folder>/<algo>/<env>_1`; use `--exp-id -1` only for `<folder>/<algo>/<env>.zip`. |
| `--exp-id 0` loads id 0 or reports no-experiment paths | No numeric run directory matching `<env>_<number>` was found under `<folder>/<algo>`. | List the run directories. Use a numeric Zoo layout or pass an explicit positive id that exists. Beware ad-hoc names such as `<env>_debug`, which are ignored by latest discovery. |
| `No checkpoint found for <algo> on <env>` | `--load-last-checkpoint` was requested but no `rl_model_*_steps.zip` files exist in the run folder. | Use the final model, `--load-best` if available, or create checkpoints through training with a save frequency. |
| `No model found ... rl_model_<steps>_steps.zip` | The exact `--load-checkpoint <steps>` file is absent or named differently. | Inspect available checkpoint step counts and choose one of them. The latest-checkpoint selector uses the integer in `rl_model_<steps>_steps.zip`. |
| `VecNormalize stats ... vecnormalize.pkl not found` | The saved config says normalization was used, but the stats file is missing from `<run>/<env>/`. | Locate/copy the matching `vecnormalize.pkl` from the training run, choose a non-normalized model, or retrain/export correctly. `--norm-reward` cannot create missing stats. |
| Model load fails with schedule/clip range/learning rate pickling errors | Older saved models or Python-version transitions can require patched custom objects at load time. | Add `--custom-objects`. Recent Python versions may apply common safe custom objects automatically, but the explicit flag is useful when diagnosing older artifacts. |
| Off-policy load mentions `buffer_size=1` or replay-buffer-related defaults | Evaluation intentionally uses a dummy buffer for off-policy algorithms because replay memory is not needed for prediction. | Treat this as expected for enjoy/evaluation. Do not require `replay_buffer.pkl` unless continuing training, which belongs to `training-cli`. |
| Empty window/display errors, `cannot connect to X server`, or renderer crash | Rendering was requested in a headless environment. | Add `--no-render`. Route actual video capture or display-dependent workflows to `integrations-hub-tracking`. |
| Local pretrained model path under `rl-trained-agents` is absent and command tries to download from Hub | `enjoy` treats missing models under a path containing `rl-trained-agents` as pretrained-agent lookup and attempts SB3 Hub fallback. | For offline local evaluation, pass `-f <local logs>` that does not imply the pretrained-agent tree, or explicitly allow/route Hub download to `integrations-hub-tracking`. |
| `benchmark` contacts the Hub even with `--test-mode` | `--test-mode` only limits the number of benchmark experiments; it does not disable Hub enumeration/download. | Add `--no-hub` for local/offline smoke tests and set `--log-dir` to a real local model tree. |
| Progress bar import error | `-P`/`--progress` requires progress-bar optional packages. | Omit `-P` for minimal smoke tests or install the optional progress dependencies in the runtime environment. |
| Environment id or wrapper import failure during enjoy | The saved config depends on custom env packages, wrappers, or env kwargs that are not available. | Import needed env packages with `--gym-packages` or use the custom-components/config sub-skills to validate custom components and config. |

## Interpreting config and normalization warnings

Missing `args.yml` or `config.yml` is not always fatal for a very simple, non-normalized model, but it is risky. Evaluation may silently miss:

- custom `env_kwargs`,
- wrappers or vectorized environment wrappers,
- frame stacking,
- normalization settings,
- monitor kwargs or goal/success logging conventions.

When the model came from a proper RL Zoo training run or Hub download, expect `<run>/<env>/args.yml` and `<run>/<env>/config.yml` to exist. Treat a missing `vecnormalize.pkl` as a hard error whenever `normalize` is true in saved config.

## Headless local command template

```bash
python -m rl_zoo3.enjoy \
  --algo <algo> --env <env-id> \
  -f <folder> --exp-id <id> \
  --no-render --deterministic \
  -n 1000 --seed 0
```

Use a selector only when its file exists:

```bash
--load-best
--load-checkpoint <steps>
--load-last-checkpoint
```

## Offline benchmark template

```bash
python -m rl_zoo3.benchmark \
  --log-dir <folder> \
  --benchmark-dir <folder>/benchmark \
  --test-mode --no-hub \
  -n 100 --num-threads 2
```

If this command produces an empty benchmark table, inspect whether `<folder>` contains at least one algorithm directory with a run folder and one nested `args.yml` file.
