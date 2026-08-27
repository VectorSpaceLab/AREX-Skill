# Configuration Reference

This repository uses Hydra for training and evaluation composition. The workspace config selects the method, and the task config selects the dataset and env runner.

## Hydra composition model

- `train.py` reads from the repo-local config root and uses `@hydra.main`.
- `task=<task_name>` replaces the task subtree with `config/task/<task_name>.yaml`.
- `--config-name=<workspace>` selects the workspace YAML under `config/`.
- `ray_train_multirun.py` composes the same workspace config once, writes a shared `config.yaml`, and then launches seeded training workers with per-run overrides.

Use the bundled helper [`../scripts/compose_experiment_config.py`](../scripts/compose_experiment_config.py) to inspect the composed config without starting training.

```console
python ../scripts/compose_experiment_config.py \
  --config-root diffusion_policy/config \
  --config-name train_diffusion_unet_lowdim_workspace \
  --override task=pusht_lowdim \
  --override training.seed=42 \
  --print-targets
```

## Workspace config anatomy

Common top-level fields in workspace YAMLs:

| Field | Meaning |
|---|---|
| `name` | Run family name used in logging and output paths |
| `_target_` | Workspace class path instantiated by Hydra |
| `task_name` | Convenience alias for `task.name` |
| `policy` | Policy and model tree |
| `ema` | EMA wrapper config when enabled |
| `dataloader`, `val_dataloader` | PyTorch loader settings |
| `optimizer` | Optimizer class and hyperparameters |
| `training` | Device, seed, evaluation cadence, checkpoint cadence, resume, EMA, debug flags |
| `logging` | W&B project/name/group/id/mode/resume |
| `checkpoint` | Top-k monitor key, mode, file naming, last-ckpt policy |
| `multi_run` | Ray multirun output root and W&B name base |
| `hydra` | Default Hydra run and sweep directories |

Important `training` keys seen across the repo:

- `device`
- `seed`
- `resume`
- `use_ema`
- `lr_scheduler`
- `lr_warmup_steps`
- `num_epochs`
- `gradient_accumulate_every`
- `rollout_every`
- `checkpoint_every`
- `val_every`
- `sample_every`
- `max_train_steps`
- `max_val_steps`
- `tqdm_interval_sec`
- `freeze_encoder` for pretrained image workspaces
- `eval_every` and `eval_first` for the video workspace variant

## Task config anatomy

Task YAMLs supply the benchmark-specific runtime objects and shapes.

| Field | Meaning |
|---|---|
| `name` | Task family name used in output naming |
| `obs_dim`, `action_dim` | Low-dim interface sizes when applicable |
| `shape_meta` | Image / low-dim observation structure for image and hybrid tasks |
| `dataset_path` | Dataset or replay path for Robomimic and real-data tasks |
| `dataset` | Dataset class and sampling parameters |
| `env_runner` | Evaluation runner class and rollout parameters |

Task configs usually own:

- `dataset._target_`
- `env_runner._target_`
- `dataset_path` when the task is not self-contained
- rollout settings such as `n_train`, `n_test`, `max_steps`, `n_obs_steps`, `n_action_steps`, and `test_start_seed`

## Common config families

| Workspace | Typical task family | Observation family |
|---|---|---|
| `train_diffusion_unet_lowdim_workspace` | Push-T, BlockPush, low-dim Robomimic, Kitchen, Square, Can, Transport | low-dim |
| `train_diffusion_unet_image_workspace` | Push-T image, Lift image, Square image, Can image, Tool Hang image, Transport image | image |
| `train_diffusion_unet_hybrid_workspace` | Hybrid Robomimic / mixed image-lowdim tasks | hybrid |
| `train_diffusion_transformer_lowdim_workspace` | Low-dim tasks | low-dim |
| `train_diffusion_transformer_hybrid_workspace` | Hybrid tasks | hybrid |
| `train_bet_lowdim_workspace` | BlockPush low-dim style benchmarks | low-dim |
| `train_robomimic_lowdim_workspace` | Robomimic low-dim datasets | low-dim |
| `train_robomimic_image_workspace` | Robomimic image datasets | image |
| `train_diffusion_unet_video_workspace` | Video benchmark variant | image/video |
| `train_*_real_*` | Captured real-data datasets | image or hybrid |

## Key output and logging fields

- `hydra.run.dir` and `multi_run.run_dir` should stay aligned with the output layout you want.
- `logging.name`, `logging.id`, and `logging.group` are passed directly to W&B.
- `logging.mode` controls online vs offline behavior.
- `checkpoint.topk.monitor_key` must match a metric that is actually logged by the selected env runner.
- `checkpoint.topk.format_str` controls the top-k checkpoint filenames.

Common checkpoint settings in the repo:

- `monitor_key: test_mean_score` for most tasks.
- `monitor_key: test_score` for the video variant.
- `mode: max` for success-rate style metrics.
- `save_last_ckpt: True` for most training families.

## Output tree expectations

Single-run training writes:

```text
run_dir/
├── .hydra/
├── checkpoints/
├── logs.json.txt
├── media/
├── train.log
└── wandb/
```

Evaluation writes:

```text
output_dir/
├── eval_log.json
└── media/
```

Ray multirun writes:

```text
multi_run.run_dir/
├── config.yaml
├── metrics/
├── train_0/
├── train_1/
└── train_2/
```

## Config inspection checklist

When a command fails before training starts, check these items first:

1. The chosen workspace `_target_` matches the method family.
2. The `task` config contains the right dataset and env runner targets.
3. `task.dataset_path` exists for dataset-backed tasks.
4. `training.device` is valid for the current machine.
5. `logging.mode` and W&B settings match the intended online/offline behavior.
6. `checkpoint.topk.monitor_key` matches a metric emitted by the env runner.
7. `hydra.run.dir` and `multi_run.run_dir` are writable and unique.

The bundled config helper can print these values and reveal missing `task.dataset_path` entries without launching training.
