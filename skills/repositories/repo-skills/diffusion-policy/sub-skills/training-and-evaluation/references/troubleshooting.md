# Training and Evaluation Troubleshooting

Start every diagnosis by composing the config safely:

```console
python ../scripts/compose_experiment_config.py \
  --config-root diffusion_policy/config \
  --config-name train_diffusion_unet_lowdim_workspace \
  --override task=pusht_lowdim \
  --print-targets
```

This checks targets and selected scalar fields without instantiating a workspace or starting training.

## Symptom-to-fix table

| Symptom | Likely cause | Fix |
|---|---|---|
| Hydra cannot find the config | Wrong `--config-name`, wrong `--config-dir` / config root, or `.yaml` suffix mismatch | Use the exact workspace config basename, pass the correct config root, and verify with `compose_experiment_config.py --print-targets` |
| `task.dataset_path` is missing | The selected task family does not define a path, or the wrong task override was used | Choose a dataset-backed task such as a Robomimic or real-data task, or pass `task.dataset_path=<path>` when that task supports it |
| Dataset target or env runner target looks wrong | Workspace observation family and task family do not match | Pair low-dim workspaces with low-dim tasks, image/hybrid workspaces with image/hybrid tasks, and real-data configs with captured real-data tasks |
| `output_dir` already exists during checkpoint evaluation | `eval.py` intentionally prompts before overwriting | Use a fresh `--output_dir`, delete/rename the old output, or explicitly confirm the prompt in an interactive run |
| Training run directory collides or logs append unexpectedly | Fixed `hydra.run.dir` or `multi_run.run_dir` was reused | Use a unique timestamped run directory or intentionally resume with `training.resume=True` after confirming the checkpoint state |
| W&B login/authentication error | `logging.mode=online` requires credentials and network access | Run `wandb login`, or use `logging.mode=offline` / `WANDB_MODE=offline` for local-only runs |
| W&B metrics monitor behaves differently from local summary | `ray_train_multirun.py` starts a source metrics worker that logs to project `diffusion_policy_metrics` | For local-only inspection, use `../scripts/summarize_multirun_metrics.py` on the finished `multi_run.run_dir` |
| Ray worker cannot see the dataset | Worker cwd does not contain `data`, or `--data_src` points to the wrong location | Pass `--data_src=<dataset_root>`; `ray_exec.py` creates a `data` symlink inside each worker cwd |
| Metrics aggregation is empty | `train_*/logs.json.txt` does not exist yet, contains no complete JSON lines, or the selected `--key` is not logged | Wait for train workers to write logs, verify the key spelling such as `test/mean_score`, and run the bundled summarizer offline |
| Missing MuJoCo / Robomimic / simulator import | Optional simulator dependencies or system OpenGL/MuJoCo packages are absent | Use the full Linux simulation environment for benchmarks; MuJoCo-style stacks need packages such as `libosmesa6-dev`, `libgl1-mesa-glx`, `libglfw3`, and `patchelf` |
| Segfault or rendering failure from a simulator env runner | Forked vector envs can inherit OpenGL contexts; Robomimic/robosuite rendering is sensitive | Reduce parallel envs, disable rendering where possible, or use the task runner's dummy/no-render path when available |
| `cuda:0` is unavailable | `training.device` or `eval.py --device` names a GPU that PyTorch cannot use | Set `training.device=cpu`, choose an existing GPU, set `CUDA_VISIBLE_DEVICES`, or install a CUDA-compatible PyTorch stack |
| CPU run is extremely slow or fails for benchmark workflows | Benchmarks are intended for Linux + NVIDIA GPU with simulator dependencies | Treat CPU as a config/debug substitute only unless the selected task is explicitly lightweight |
| `eval.py` fails to load checkpoint payload | Checkpoint path is wrong, checkpoint is incomplete, or code/config family does not match the payload | Use a complete `latest.ckpt` or top-k `.ckpt` from the run's `checkpoints/`; do not edit the checkpoint config manually |
| Evaluation metric is unexpectedly low | The checkpoint uses the wrong task config, wrong device, or non-EMA weights | Confirm `eval.py` loads the payload config, check `cfg.training.use_ema`, and verify the env runner target and dataset/task assumptions |
| Ray option `--monitor_max_retries` is rejected | The source option is misspelled | Use the exact source spelling `--monitor_max_retires` or avoid overriding it |

## Missing dataset path diagnosis

If a training command fails with a missing path, inspect these config nodes:

- `task.name`
- `task.dataset_path`
- `task.dataset._target_`
- `task.env_runner._target_`
- `training.device`

Examples:

```console
python ../scripts/compose_experiment_config.py \
  --config-root diffusion_policy/config \
  --config-name train_robomimic_lowdim_workspace \
  --override task=square_lowdim \
  --print-targets
```

```console
python ../scripts/compose_experiment_config.py \
  --config-root diffusion_policy/config \
  --config-name train_diffusion_unet_real_image_workspace \
  --override task=real_pusht_image \
  --override task.dataset_path=data/pusht_real/my_dataset \
  --print-targets
```

If `task.dataset_path` prints as missing, the selected task likely uses a zarr path inside `task.dataset` instead of a standalone `dataset_path`, or the wrong task family was selected. Dataset schema and conversion details belong to the data-and-replay-buffers sub-skill.

## Multirun output-tree diagnosis without Ray

You can inspect a completed or partial multirun tree without starting Ray:

```console
python ../scripts/summarize_multirun_metrics.py \
  --run-dir data/outputs/2023.03.01/22.13.58_train_diffusion_unet_hybrid_pusht_image \
  --key test/mean_score
```

Expected files:

```text
run_dir/
├── config.yaml
├── metrics/
│   ├── logs.json.txt
│   ├── metrics.json
│   └── metrics.log
├── train_0/logs.json.txt
├── train_1/logs.json.txt
└── train_2/logs.json.txt
```

If `metrics/` is missing but `train_*` logs exist, the training workers ran and the monitor did not complete; the bundled summarizer can still report per-run statistics.

## W&B safe modes

- Online logging: `logging.mode=online` plus working credentials.
- Offline logging: `logging.mode=offline` or environment variable `WANDB_MODE=offline`.
- Disabled W&B is not a standard repo config path; prefer offline mode for reproducible local testing.
- Ray multirun's source monitor worker always builds a W&B-enabled monitor command, so use local summarization when network isolation is required.

## Checkpoint evaluation overwrite rule

`eval.py` calls an explicit confirmation when `--output_dir` exists. This is expected. For automated or non-interactive use, choose a new output directory per checkpoint evaluation instead of relying on prompts.
