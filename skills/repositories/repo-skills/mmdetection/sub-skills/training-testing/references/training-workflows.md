# Training Workflows

MMDetection 3.3.0 training is driven by `tools/train.py`, which loads a config, merges `--cfg-options`, determines `work_dir`, optionally enables AMP and auto LR scaling, sets resume state, builds an MMEngine runner, and calls `runner.train()`.

## Preflight checklist

| Check | Why it matters | Action |
|---|---|---|
| Config path exists | `tools/train.py` requires a Python config file | Inspect via configuration-model-zoo if the config needs edits |
| Dataset is prepared | Training dataloaders fail late when annotations or image roots are missing | Route dataset layout questions to datasets-evaluation |
| Full `mmcv` is installed | `mmcv-lite` cannot provide compiled ops and can fail with `mmcv._ext` | Install full `mmcv` compatible with the torch/CUDA stack |
| `work_dir` is explicit | Logs and checkpoints otherwise default to `./work_dirs/<config-stem>` | Pass `--work-dir work_dirs/<experiment>` |
| Checkpoint intent is clear | `resume` and fine-tuning use different state | Use `--resume` for continuing optimizer/epoch state; use config `load_from` for fine-tuning weights |
| Batch size and LR are aligned | Default schedules usually assume base batch size 16 | Check `auto_scale_lr.base_batch_size` before `--auto-scale-lr` |

## Single GPU training

```bash
python tools/train.py CONFIG.py \
  --work-dir work_dirs/EXP_NAME \
  --cfg-options train_dataloader.batch_size=2
```

Useful flags from `tools/train.py`:

| Flag | Meaning |
|---|---|
| `--work-dir DIR` | Overrides where logs, checkpoints, visualizer outputs, and evaluation records are written |
| `--amp` | Converts the optimizer wrapper to dynamic-loss-scale AMP training |
| `--auto-scale-lr` | Sets `cfg.auto_scale_lr.enable=True`; requires `auto_scale_lr.enable` and `auto_scale_lr.base_batch_size` in the config |
| `--resume` | Auto-resumes from the latest checkpoint under `work_dir` |
| `--resume CHECKPOINT.pth` | Resumes model, optimizer, scheduler, and iteration/epoch state from a specific checkpoint |
| `--cfg-options key=value ...` | Merges overrides into the config after loading it |

`--cfg-options` accepts nested keys such as `train_dataloader.batch_size=4`, `train_cfg.max_epochs=24`, or `optim_wrapper.optimizer.lr=0.005`. Quote list-like values in the user's shell when needed.

## CPU debug training

```bash
CUDA_VISIBLE_DEVICES=-1 python tools/train.py CONFIG.py \
  --work-dir work_dirs/cpu_debug \
  --cfg-options train_dataloader.num_workers=0 val_dataloader.num_workers=0
```

CPU training follows the same code path as single-GPU training after GPUs are disabled. It is intended for smoke tests and debugging only; detector training is usually too slow for real experiments on CPU.

## Resume versus fine-tuning

| Goal | Correct mechanism | Notes |
|---|---|---|
| Continue an interrupted run from the latest checkpoint | `--resume` with the same `--work-dir` | Sets `cfg.resume=True` and clears `cfg.load_from` |
| Continue from a specific interrupted checkpoint | `--resume path/to/epoch_N.pth` | Restores optimizer/scheduler and epoch/iteration counters |
| Start a new fine-tuning run from pretrained weights | Put `load_from='path-or-url'` in the config | Training starts from epoch/iter zero; do not use `--resume` |
| Change dataset/classes and reuse backbone/head-compatible weights | Edit config and set `load_from` | Head shape mismatches may require config changes or checkpoint surgery |

In `tools/train.py`, `--resume CHECKPOINT` sets `cfg.resume=True` and `cfg.load_from=CHECKPOINT`; MMEngine interprets this as resume state, not a fresh fine-tune.

## Learning-rate scaling

Most base schedules assume 8 GPUs × 2 samples/GPU, i.e. `auto_scale_lr.base_batch_size=16`. Use `--auto-scale-lr` only after confirming the config or its bases define both `auto_scale_lr.enable` and `auto_scale_lr.base_batch_size`.

Example: resume the latest checkpoint while changing the per-GPU batch size and enabling auto scaling.

```bash
python tools/train.py configs/example.py \
  --work-dir work_dirs/example_resume \
  --resume \
  --auto-scale-lr \
  --cfg-options train_dataloader.batch_size=4
```

If the config lacks `auto_scale_lr`, `tools/train.py` raises a runtime error instead of silently scaling.

## PyTorch distributed training

`tools/dist_train.sh` expands to `python -m torch.distributed.launch` with `--launcher pytorch` and the environment variables below.

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 PORT=29500 bash tools/dist_train.sh CONFIG.py 4 \
  --work-dir work_dirs/EXP_NAME \
  --auto-scale-lr
```

| Variable | Default | Purpose |
|---|---:|---|
| `GPUS` argument | required | Number of processes on the node |
| `PORT` | `29500` | Master port; change it for concurrent jobs |
| `NNODES` | `1` | Number of machines |
| `NODE_RANK` | `0` | Rank of this machine |
| `MASTER_ADDR` | `127.0.0.1` | Address of rank 0 |

For two 4-GPU jobs on one 8-GPU node, reserve non-overlapping devices and ports:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 PORT=29500 bash tools/dist_train.sh CONFIG_A.py 4 --work-dir work_dirs/job_a
CUDA_VISIBLE_DEVICES=4,5,6,7 PORT=29501 bash tools/dist_train.sh CONFIG_B.py 4 --work-dir work_dirs/job_b
```

For multi-node Ethernet training, set the same `MASTER_ADDR` and `PORT` on all nodes, set `NNODES` to the machine count, and give each machine a unique `NODE_RANK`.

## Slurm training

`tools/slurm_train.sh` runs `srun` and calls `python -u tools/train.py CONFIG --work-dir=WORK_DIR --launcher=slurm ...`.

```bash
GPUS=16 GPUS_PER_NODE=8 CPUS_PER_TASK=5 bash tools/slurm_train.sh \
  PARTITION JOB_NAME CONFIG.py work_dirs/EXP_NAME \
  --auto-scale-lr
```

Slurm wrapper inputs and variables:

| Item | Meaning |
|---|---|
| Positional `PARTITION JOB_NAME CONFIG WORK_DIR` | Required scheduler partition, job label, config, and output directory |
| `GPUS` | Total tasks/GPUs requested; default 8 |
| `GPUS_PER_NODE` | GPUs per node; default 8 |
| `CPUS_PER_TASK` | CPU workers per process; default 5 |
| `SRUN_ARGS` | Extra scheduler flags such as account, time, or exclude |
| trailing args | Forwarded to `tools/train.py` after `--launcher=slurm` |

For concurrent Slurm jobs, prefer distinct communication ports through forwarded config options. In MMDetection 3.x / MMEngine-style configs, set `env_cfg.dist_cfg.port`; older migrated configs or docs may still use `dist_params.port`.

```bash
GPUS=4 bash tools/slurm_train.sh PARTITION job_a CONFIG_A.py work_dirs/job_a --cfg-options env_cfg.dist_cfg.port=29500
GPUS=4 bash tools/slurm_train.sh PARTITION job_b CONFIG_B.py work_dirs/job_b --cfg-options env_cfg.dist_cfg.port=29501
```

## Output layout

`work_dir` contains training logs, checkpoints such as `epoch_*.pth` and `latest.pth`, validation metric logs, and visualizer outputs. If `--work-dir` is omitted and the config has no `work_dir`, MMDetection uses `./work_dirs/<config-stem>`.
