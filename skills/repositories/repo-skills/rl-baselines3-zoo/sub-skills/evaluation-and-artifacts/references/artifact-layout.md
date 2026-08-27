# Artifact layout

RL Zoo evaluation code expects a small convention around the log root, algorithm, environment id, and experiment id. The same layout can come from local training or from a Hub download that was saved into a local folder.

## Standard run folder layout

For a normal numbered training run:

```text
<folder>/
  <algo>/
    <env>_<exp-id>/
      <env>.zip                      # final model, default enjoy target
      best_model.zip                 # optional best model from eval callback
      rl_model_<steps>_steps.zip     # optional checkpoints
      replay_buffer.pkl              # optional; for continuing off-policy training, not needed for enjoy
      evaluations.npz                # optional evaluation callback data
      *.monitor.csv or *.csv         # optional Monitor/reward logs
      <env>/
        args.yml                     # saved CLI arguments
        config.yml                   # saved hyperparameters/config used for env recreation
        command.txt                  # saved training command
        env_kwargs.yml               # optional; commonly present after Hub download/export
        vecnormalize.pkl             # required when config says normalization was used
```

For no-experiment layouts (`--exp-id -1`, or `--exp-id 0` when no numbered run exists), the run folder is `<folder>/<algo>` and the default final model path is `<folder>/<algo>/<env>.zip`.

## What each file means

| Path | Role during evaluation | Missing-file consequence |
| --- | --- | --- |
| `<run>/<env>.zip` | Final model loaded when no selector is passed. | Default enjoy fails with `No model found ... path: ...`. |
| `<run>/best_model.zip` | Best-evaluation model loaded by `--load-best`. | `--load-best` fails; final model may still work. |
| `<run>/rl_model_<steps>_steps.zip` | Checkpoint loaded by `--load-checkpoint <steps>`. | That exact checkpoint selector fails. |
| `<run>/rl_model_*_steps.zip` | Candidate set for `--load-last-checkpoint`. | Latest-checkpoint selector fails when none exist. |
| `<run>/<env>/args.yml` | Saved CLI arguments, including environment kwargs. | Evaluation can lose training-time `env_kwargs`; model may run against a different environment. |
| `<run>/<env>/config.yml` | Saved hyperparameters, wrappers, normalization flag, frame stack, env kwargs. | Simple models may load, but wrappers/normalization/frame-stack/custom settings can be wrong or fail. |
| `<run>/<env>/env_kwargs.yml` | Export/download metadata for environment kwargs. | Usually optional for local enjoy; useful for Hub packaging. |
| `<run>/<env>/vecnormalize.pkl` | Saved VecNormalize statistics. | Required when normalization is enabled; missing stats raise a VecNormalize error. |
| `<run>/evaluations.npz` | Evaluation callback scores over training. | Plotting/benchmark interpretation may be incomplete; enjoy does not require it. |
| `<run>/*.csv` or reward-log folders | Monitor/reward data. | Benchmark/plotting may have no reward history; enjoy can still step the model. |

## `--exp-id` and latest run discovery

`--exp-id 0` means “discover the latest numeric run id”. It scans `<folder>/<algo>` for directories named exactly like `<env>_<number>` and chooses the greatest number.

Examples:

```text
logs/ppo/CartPole-v1_1/       # picked if highest numeric id is 1
logs/ppo/CartPole-v1_2/       # picked over _1
logs/ppo/CartPole-v1_debug/   # ignored by numeric latest discovery
```

If no numeric run is found, effective id remains `0`, and the no-experiment layout `<folder>/<algo>/<env>.zip` is used. When debugging a “latest” surprise, inspect the actual directory names and either rename/copy into a numeric run layout or pass an explicit positive experiment id that matches a numbered run.

## Checkpoint selection details

Checkpoint names must match `rl_model_<integer>_steps.zip`. The latest checkpoint selector sorts by the integer step count inside the filename, not by modification time or alphabetical order.

Good names:

```text
rl_model_500_steps.zip
rl_model_1000_steps.zip
rl_model_10000_steps.zip
```

Names that are ignored by latest-checkpoint selection:

```text
rl_model_latest.zip
checkpoint_1000.zip
rl_model_1000.zip
```

## Local pretrained-agent and Hub-download layouts

A local `rl-trained-agents/` tree, when present, uses the same `<folder>/<algo>/<env>_<id>/...` convention. However, ordinary installed-package use may not include that folder. If `enjoy` targets a folder whose path contains `rl-trained-agents` and the selected model is missing, it may try to download from the SB3 Hub. That is a network side effect and should be handled by the `integrations-hub-tracking` sub-skill or avoided with an explicit local `-f <logs>` folder.

Hub download/export flows can add `env_kwargs.yml` and unpack metrics such as `evaluations.npz` and Monitor CSV files. Those files are useful, but the local no-render evaluation path still hinges on the selected model file plus any saved config/normalization files required to recreate the environment.

## Inspecting a tree without loading weights

The bundled inspector checks the same naming conventions without importing `rl_zoo3`, importing Stable-Baselines3, contacting the network, or loading model zip contents.

```bash
python scripts/model_artifact_inspector.py \
  --folder logs --algo ppo --env CartPole-v1 --exp-id 0
```

Selector examples:

```bash
# Verify best-model target
python scripts/model_artifact_inspector.py \
  --folder logs --algo a2c --env Pendulum-v1 --exp-id 1 --load-best

# Verify specific checkpoint target
python scripts/model_artifact_inspector.py \
  --folder logs --algo a2c --env Pendulum-v1 --exp-id 1 --load-checkpoint 500

# Verify latest checkpoint target
python scripts/model_artifact_inspector.py \
  --folder logs --algo a2c --env Pendulum-v1 --exp-id 1 --load-last-checkpoint
```

Use `--strict` when you want missing selected artifacts or config-indicated VecNormalize stats to produce a non-zero exit status. Use `--json` for machine-readable output in verification cases.
