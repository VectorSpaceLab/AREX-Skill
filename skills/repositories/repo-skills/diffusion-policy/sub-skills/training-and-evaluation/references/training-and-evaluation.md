# Training and Evaluation Workflows

This sub-skill covers the command shapes and run artifacts used to train, evaluate, and summarize Diffusion Policy experiments.

## Command map

The upstream project exposes script-style entrypoints rather than installed console commands. Use these command shapes only when the user is operating in a compatible Diffusion Policy checkout or equivalent project layout that provides the entrypoint and config files. Use bundled helpers first for safe inspection.

| Upstream entrypoint role | Purpose | Important flags | Main outputs |
|---|---|---|---|
| training entrypoint (`train.py` in the upstream layout) | Hydra single-run training | `--config-name`, `task=...`, `training.seed=...`, `training.device=...`, `hydra.run.dir=...` | `checkpoints/`, `logs.json.txt`, `.hydra/`, `media/`, `wandb/` |
| evaluation entrypoint (`eval.py` in the upstream layout) | Evaluate one checkpoint | `-c/--checkpoint`, `-o/--output_dir`, `-d/--device` | `eval_log.json`, `media/` |
| Ray multirun entrypoint (`ray_train_multirun.py` in the upstream layout) | Seed sweep + metric monitor | `--config-name`, `--config-dir`, `--seeds`, `--monitor_key`, `--data_src`, `--single_node`, overrides after `--` | `config.yaml`, `train_*/`, `metrics/` |
| Ray worker helper (`ray_exec.py` in the upstream layout) | Low-level Ray worker wrapper | `--data_src`, `--ray_address`, `--num_cpus`, `--num_gpus`, `--unbuffer_python` | Worker subprocess output only |
| metrics entrypoint (`multirun_metrics.py` in the upstream layout) | Source-side rolling aggregate | `--input`, `--key`, `--use_wandb`, `--project`, `--group` | `metrics/logs.json.txt`, `metrics/metrics.json`, `metrics/metrics.log` |

## Single-seed training

The upstream training entrypoint is Hydra-based. The workspace config chooses the method, and the task config chooses the dataset and env runner.

Typical low-dim command shape:

```console
python <training-entrypoint> \
  --config-name=train_diffusion_unet_lowdim_workspace \
  task=pusht_lowdim \
  training.seed=42 \
  training.device=cuda:0 \
  hydra.run.dir=data/outputs/$(date +%Y.%m.%d)/$(date +%H.%M.%S)_train_diffusion_unet_lowdim_pusht_lowdim
```

Typical image command shape:

```console
python <training-entrypoint> \
  --config-name=train_diffusion_unet_image_workspace \
  task=lift_image_abs \
  training.seed=42 \
  training.device=cuda:0 \
  hydra.run.dir=data/outputs/$(date +%Y.%m.%d)/$(date +%H.%M.%S)_train_diffusion_unet_image_lift_image_abs
```

Useful overrides:

- `task=<task_name>` swaps in `config/task/<task_name>.yaml`.
- `training.seed=<int>` controls RNG seeding.
- `training.device=cuda:0` or `cpu` selects the model/optimizer device.
- `logging.mode`, `logging.project`, `logging.name`, `logging.id`, `logging.group` control W&B routing.
- `checkpoint.topk.monitor_key` controls which metric saves top-k checkpoints.
- `training.resume=True` resumes from `checkpoints/latest.ckpt` when present.

The main training loop behavior is:

- build dataset and validation dataset from `cfg.task.dataset`
- call `dataset.get_normalizer()` and pass it to the policy
- create `cfg.task.env_runner` and call `env_runner.run(policy)` at the configured rollout interval
- write `logs.json.txt` one JSON object per line with numeric metrics
- save `latest.ckpt` plus any top-k checkpoint files under `checkpoints/`

Typical training tree:

```text
run_dir/
├── .hydra/
├── checkpoints/
│   ├── latest.ckpt
│   └── epoch=0000-test_mean_score=0.123.ckpt
├── logs.json.txt
├── media/
├── train.log
└── wandb/
```

## Checkpoint evaluation

The upstream evaluation entrypoint evaluates a single saved checkpoint with the task's configured env runner.

```console
python <evaluation-entrypoint> \
  --checkpoint data/.../checkpoints/latest.ckpt \
  --output_dir data/pusht_eval_output \
  --device cuda:0
```

Notes:

- If `--output_dir` already exists, the script prompts before overwrite.
- The checkpoint payload supplies the config, so evaluation reuses the exact workspace and task structure that produced the checkpoint.
- If `cfg.training.use_ema` is enabled in the checkpoint config, evaluation uses `workspace.ema_model`; otherwise it uses `workspace.model`.
- `env_runner.run(policy)` returns metrics and optional videos; `eval.py` stores them in `eval_log.json` and `media/`.

Typical evaluation tree:

```text
output_dir/
├── eval_log.json
└── media/
    ├── rollout_0.mp4
    └── ...
```

## Ray multirun and metrics

The upstream Ray multirun entrypoint is the project workflow for multi-seed sweeps.

Start a local Ray cluster first when using local GPUs:

```console
export CUDA_VISIBLE_DEVICES=0,1,2
ray start --head --num-gpus=3
```

Example multirun launch:

```console
python <ray-multirun-entrypoint> \
  --config-name=train_diffusion_unet_lowdim_workspace \
  --seeds=42,43,44 \
  --monitor_key=test/mean_score \
  --data_src=./data \
  --single_node \
  -- \
  task=pusht_lowdim \
  training.device=cuda:0 \
  logging.mode=online
```

Important Ray flags and behaviors:

- `--config-dir` can be used when composing from a different local config root; otherwise the script uses the repo-local config directory.
- `--seeds` is comma-separated and becomes one `train_i` worker per seed.
- `--monitor_key` is repeatable and drives the metric monitor worker.
- The source option spelling is `--monitor_max_retires`.
- `--single_node` packs the training workers and the monitor onto one machine.
- `ray_exec.py` symlinks `data_src` to `data` inside each worker working directory before running the subprocess.
- Each train worker writes to `multi_run.run_dir/train_i/`.
- The metrics worker writes aggregated logs into `multi_run.run_dir/metrics/` and also logs to W&B project `diffusion_policy_metrics` in the source workflow.

Typical Ray multirun tree:

```text
multi_run.run_dir/
├── config.yaml
├── metrics/
│   ├── logs.json.txt
│   ├── metrics.json
│   └── metrics.log
├── train_0/
│   ├── checkpoints/
│   ├── logs.json.txt
│   └── train.log
├── train_1/
└── train_2/
```

The source `multirun_metrics.py` computes rolling metrics from all `train_*` logs. The paper-facing values commonly come from `max` and `k_min_train_loss` aggregations.

Use the bundled offline helper [`../scripts/summarize_multirun_metrics.py`](../scripts/summarize_multirun_metrics.py) when you only need to inspect local `train_*/logs.json.txt` files without W&B or Ray.

## Benchmark routing

Choose the workspace family to match the benchmark family:

- Low-dim simulation: `train_diffusion_unet_lowdim_workspace`, `train_diffusion_transformer_lowdim_workspace`, `train_ibc_dfo_lowdim_workspace`, `train_bet_lowdim_workspace`, `train_robomimic_lowdim_workspace`.
- Image simulation: `train_diffusion_unet_image_workspace`, `train_diffusion_unet_hybrid_workspace`, `train_diffusion_transformer_hybrid_workspace`, `train_robomimic_image_workspace`.
- Video benchmark variant: `train_diffusion_unet_video_workspace`.
- Real-data training on captured datasets: `train_diffusion_unet_real_*`, `train_diffusion_transformer_real_hybrid_workspace`, `train_ibc_dfo_real_hybrid_workspace`, `train_robomimic_real_image_workspace`.

Task config names route the benchmark specifics:

- `pusht_lowdim`, `pusht_image`
- `blockpush_lowdim_seed`
- `lift_*`, `square_*`, `can_*`, `tool_hang_*`, `transport_*`
- `kitchen_lowdim`
- `real_pusht_image`

The task config owns `dataset._target_`, `env_runner._target_`, and any task-specific `dataset_path` or `shape_meta`. Match the workspace family to the observation family and the task config to the dataset/evaluation family.

## Core API names and files

- `BaseWorkspace`
- `BaseLowdimDataset` / `BaseImageDataset`
- `BaseLowdimPolicy` / `BaseImagePolicy`
- `BaseLowdimRunner` / `BaseImageRunner`
- `LinearNormalizer`
- `TopKCheckpointManager`
- `JsonLogger` and `read_json_log`
- `train.py`, `eval.py`, `ray_train_multirun.py`, `ray_exec.py`, `multirun_metrics.py`
