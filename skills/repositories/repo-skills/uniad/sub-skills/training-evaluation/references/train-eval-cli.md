# UniAD train/eval CLI reference

## Source evidence

This reference is distilled from `README.md`, `docs/INSTALL.md`, `docs/TRAIN_EVAL.md`, `tools/train.py`, `tools/test.py`, `tools/uniad_dist_train.sh`, `tools/uniad_dist_eval.sh`, `tools/uniad_slurm_train.sh`, and `tools/uniad_slurm_eval.sh`.

## Command family map

| Surface | Purpose | Default behavior |
| --- | --- | --- |
| `tools/train.py` | Train a UniAD config directly | Non-distributed by default; `--gpus` / `--gpu-ids` only matter when `--launcher none` |
| `tools/test.py` | Evaluate a checkpoint directly | Distributed-only in practice; non-distributed branch asserts false |
| `tools/uniad_dist_train.sh` | Multi-GPU training wrapper | Uses `torchrun`, sets `--launcher pytorch`, forces `--deterministic`, and writes logs under the derived work dir |
| `tools/uniad_dist_eval.sh` | Multi-GPU evaluation wrapper | Uses `torchrun`, sets `--launcher pytorch`, forces `--eval bbox`, and writes results under the derived work dir |
| `tools/uniad_slurm_train.sh` | SLURM training wrapper | Uses `srun`, sets `--launcher=slurm`, and writes logs under the derived work dir |
| `tools/uniad_slurm_eval.sh` | SLURM evaluation wrapper | Uses `srun`, sets `--launcher=slurm`, `--eval bbox`, and `--show-dir` to the derived work dir |

## `tools/train.py`

### Arguments

- Positional: `config`
- Optional: `--work-dir`, `--resume-from`, `--no-validate`
- GPU controls for non-distributed runs: `--gpus`, `--gpu-ids`
- Reproducibility: `--seed` default `0`, `--deterministic`
- Config overrides: deprecated `--options`, preferred `--cfg-options`
- Launcher: `--launcher {none,pytorch,slurm,mpi}` with default `none`
- Misc: `--local_rank`, `--autoscale-lr`

### Behavior that matters

- `cfg.work_dir` precedence is CLI `--work-dir` > config `work_dir` > `./work_dirs/<config-basename>`.
- `--resume-from` is only applied when the file exists on disk.
- `--gpus` and `--gpu-ids` only affect the non-distributed path.
- `--autoscale-lr` scales the optimizer LR by `len(cfg.gpu_ids) / 8`.
- When `--launcher` is not `none`, the script calls `init_dist(...)` and reassigns `cfg.gpu_ids` from `world_size`.
- The script copies the resolved config into `work_dir` and writes a timestamped log file there.
- `cfg.checkpoint_config.meta` records framework versions and class names when checkpointing is enabled.
- `torch.multiprocessing.set_start_method('fork')` is set before the main entry point.
- `workflow` length 2 activates a validation dataset copy that borrows the training pipeline.

### Direct-training example shape

```bash
python tools/train.py \
  projects/configs/stage1_track_map/base_track_map.py \
  --launcher pytorch \
  --work-dir projects/work_dirs/stage1_track_map/base_track_map/ \
  --deterministic
```

For a non-distributed smoke run, `--launcher none` plus `--gpus 1` is the meaningful combination. If you keep `--launcher pytorch`, the GPU-count flags do not control the launcher.

## `tools/test.py`

### Arguments

- Positional: `config`, `checkpoint`
- Output / evaluation: `--out`, `--eval`, `--format-only`, `--show`, `--show-dir`
- Distributed collection: `--gpu-collect`, `--tmpdir`
- Reproducibility: `--seed` default `0`, `--deterministic`
- Config overrides: deprecated `--options`, preferred `--cfg-options`
- Evaluation kwargs: deprecated `--options`, preferred `--eval-options`
- Launcher: `--launcher {none,pytorch,slurm,mpi}` with default `pytorch`
- Misc: `--local_rank`, `--fuse-conv-bn`

### Behavior that matters

- `--out` must end in `.pkl` or `.pickle`.
- At least one of `--out`, `--eval`, `--format-only`, `--show`, or `--show-dir` must be present.
- `--eval` and `--format-only` are mutually exclusive.
- The config loader forces `cfg.model.pretrained = None` before model construction.
- If `cfg.data.test.samples_per_gpu > 1`, the pipeline swaps `ImageToTensor` for `DefaultFormatBundle` variants.
- Non-distributed evaluation is not implemented: the `if not distributed` branch contains `assert False`.
- Distributed evaluation wraps the model in `MMDistributedDataParallel` and uses `custom_multi_gpu_test`.
- Rank 0 alone writes `--out`, formats results, and prints evaluation metrics.
- `--eval-options` are passed through to `dataset.evaluate(...)` together with a generated `jsonfile_prefix` under `test/<config-stem>/...`.
- The script removes EvalHook-only keys (`interval`, `tmpdir`, `start`, `gpu_collect`, `save_best`, `rule`) before calling `dataset.evaluate(...)`.

### Direct-eval example shape

```bash
python tools/test.py \
  projects/configs/stage1_track_map/base_track_map.py \
  ckpts/uniad_base_track_map.pth \
  --launcher pytorch \
  --eval bbox \
  --show-dir projects/work_dirs/stage1_track_map/base_track_map/
```

## Distributed launcher wrappers

### `tools/uniad_dist_train.sh`

Inputs: `CFG`, `GPUS`, then extra Python args.

- `GPUS_PER_NODE = min(GPUS, 8)`
- `NNODES = GPUS / GPUS_PER_NODE`
- `MASTER_PORT` defaults to `28596`
- `MASTER_ADDR` defaults to `127.0.0.1`
- `RANK` defaults to `0`
- `WORK_DIR` is derived by replacing `configs` with `work_dirs` in the config path and appending a trailing slash
- Logs are written to `${WORK_DIR}logs/train.$T`
- The wrapper appends `--deterministic` and `--work-dir ${WORK_DIR}` after user extras, so the wrapper-owned defaults win

### `tools/uniad_dist_eval.sh`

Inputs: `CFG`, `CKPT`, `GPUS`, then extra Python args.

- `GPUS_PER_NODE = min(GPUS, 8)`
- `MASTER_PORT` defaults to `28596`
- `WORK_DIR` is derived the same way as train
- Logs are written to `${WORK_DIR}logs/eval.$T`
- The wrapper appends `--eval bbox` and `--show-dir ${WORK_DIR}` after user extras, so the wrapper-owned defaults win

### `tools/uniad_slurm_train.sh`

Inputs: `PARTITION`, `CFG`, `GPUS`, then extra Python args.

- `JOB_NAME='uniad_train'`
- `GPUS_PER_NODE = min(GPUS, 8)`
- `CPUS_PER_TASK` defaults to `5`
- `SRUN_ARGS` can be injected from the environment
- Uses `srun -p <partition> --gres=gpu:<GPUS_PER_NODE> --ntasks=<GPUS> --ntasks-per-node=<GPUS_PER_NODE>`
- Invokes `python -W ignore -u tools/train.py <CFG> --work-dir <WORK_DIR> --launcher="slurm" ...`
- Logs are written to `${WORK_DIR}logs/train.$T`

### `tools/uniad_slurm_eval.sh`

Inputs: `PARTITION`, `CFG`, `CKPT`, `GPUS`, then extra Python args.

- `JOB_NAME='uniad_eval'`
- `GPUS_PER_NODE = min(GPUS, 8)`
- `CPUS_PER_TASK` defaults to `5`
- `SRUN_ARGS` can be injected from the environment
- Uses the same `srun` shape as train
- Invokes `python -W ignore -u tools/test.py <CFG> <CKPT> --eval bbox --show-dir <WORK_DIR> --launcher="slurm" ...`
- Logs are written to `${WORK_DIR}logs/eval.$T`

## Flag patterns worth preserving

- `--cfg-options key=value` merges into the config before model construction.
- If the value is a list or tuple, quote the entire assignment:
  - `--cfg-options data.train.pipeline="[a,b]"`
  - `--cfg-options something="[(a,b),(c,d)]"`
- `--seed` defaults to `0` in both entry points.
- `--deterministic` is only a CUDNN / seed reproducibility hint; it does not make distributed metric aggregation identical across all GPU counts.
- `--resume-from` and `load_from` are different knobs: the first resumes optimizer state, the second initializes from a checkpoint.
