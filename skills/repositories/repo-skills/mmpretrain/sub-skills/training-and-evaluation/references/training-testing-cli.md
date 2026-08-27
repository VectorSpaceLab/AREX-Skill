# Training and evaluation command reference

This reference summarizes safe package-level launch patterns for MMPreTrain. Prefer MIM package commands (`mim train`, `mim test`, `mim run`) or the bundled command builder instead of relying on a source checkout script path.

Use `../scripts/build_train_test_command.py` when you want a reviewed command string before actually running anything.

## Decision guide

| Situation | Package-level command | Notes |
| --- | --- | --- |
| One machine, CPU | `mim train mmpretrain CONFIG --gpus 0` / `mim test mmpretrain CONFIG --checkpoint CKPT --gpus 0` | `CUDA_VISIBLE_DEVICES=-1` is also useful when a GPU is visible but should be hidden. |
| One machine, one GPU | `mim train mmpretrain CONFIG --gpus 1` / `mim test mmpretrain CONFIG --checkpoint CKPT --gpus 1` | Requires a compatible PyTorch/MMCV backend and enough memory. |
| One machine, multiple GPUs | `mim train mmpretrain CONFIG --gpus N --launcher pytorch --port PORT` | Use a unique port for concurrent jobs. |
| Slurm cluster | `mim train mmpretrain CONFIG --launcher slurm --partition PARTITION --gpus N --gpus-per-node M` | Add `--cpus-per-task` and `--srun-args` when the cluster requires them. |
| Repeated folds | `mim run mmpretrain kfold-cross-valid CONFIG --num-splits K` | Uses MMPreTrain's package-dispatched K-fold helper when available. If MIM cannot find the command in the installed package, create an explicit config with `KFoldDataset`. |

## Training options

Base pattern:

```bash
mim train mmpretrain CONFIG_FILE [MIM_OPTIONS] [TRAIN_ARGS]
```

Common train arguments passed through to MMPreTrain:

| Argument | Effect | Notes |
| --- | --- | --- |
| `CONFIG_FILE` | Path to the training config. | Required. |
| `--work-dir WORK_DIR` | Where logs and checkpoints are written. | Defaults to a `work_dirs/<config-stem>` style directory when absent. |
| `--resume [RESUME]` | Resume training. | No value means auto-resume from latest checkpoint; a path means resume from that checkpoint. |
| `--amp` | Enable mixed-precision training. | Sets the optimizer wrapper to AMP and uses dynamic loss scale when needed. |
| `--no-validate` | Skip validation during training. | Removes validation loop, dataloader, and evaluator from the run. |
| `--auto-scale-lr` | Enable automatic LR scaling. | The config should define `auto_scale_lr.base_batch_size`. |
| `--no-pin-memory` | Disable dataloader pin memory. | Useful for CPU-only or constrained environments. |
| `--no-persistent-workers` | Disable persistent dataloader workers. | Useful when workers hang or the torch version is old. |
| `--cfg-options ...` | Override config values from the command line. | Use dotted keys and quoted list/tuple values when needed. |

MIM launch options:

| MIM option | Effect |
| --- | --- |
| `--gpus N` | Number of GPUs; use `0` for CPU-only package-level launches. |
| `--launcher {none,pytorch,slurm}` | Job launcher. Use `none` for single process. |
| `--port PORT` | Distributed communication port for PyTorch/Slurm launchers. |
| `--partition`, `--gpus-per-node`, `--cpus-per-task`, `--srun-args` | Slurm resource controls. |

Examples:

```bash
# CPU-only single process
CUDA_VISIBLE_DEVICES=-1 mim train mmpretrain path/to/config.py --gpus 0

# Single machine, one visible GPU
mim train mmpretrain path/to/config.py --gpus 1 --work-dir work_dirs/run1 --amp --auto-scale-lr

# Resume an interrupted run
mim train mmpretrain path/to/config.py --resume
mim train mmpretrain path/to/config.py --resume path/to/ckpt.pth
```

## Evaluation options

Base pattern:

```bash
mim test mmpretrain CONFIG_FILE --checkpoint CHECKPOINT_FILE [MIM_OPTIONS] [TEST_ARGS]
```

Common test arguments:

| Argument | Effect | Notes |
| --- | --- | --- |
| `CONFIG_FILE` | Path to the evaluation config. | Required. |
| `--checkpoint CHECKPOINT_FILE` | Checkpoint to evaluate. | May be local or a URL when the environment can fetch it. |
| `--work-dir WORK_DIR` | Directory for evaluation metrics. | Defaults to a work-dir derived from the config when absent. |
| `--out OUT` | File to store predictions or metrics. | Required when `--out-item` is used. |
| `--out-item {metrics,pred}` | Choose what `--out` stores. | `pred` is the default behavior when `--out` is given. |
| `--cfg-options ...` | Override config values from the command line. | Same syntax as training. |
| `--amp` | Enable fp16 test mode. | Sets `test_cfg.fp16=True`. |
| `--show-dir SHOW_DIR` | Save visualization images. | Requires a visualization hook in `default_hooks`. |
| `--show` | Display predictions in a window. | Avoid in headless environments; prefer `--show-dir`. |
| `--interval INTERVAL` | Visualize every N samples. | Defaults to `1`. |
| `--wait-time WAIT_TIME` | Window display time in seconds. | Defaults to `2`. |
| `--no-pin-memory` | Disable dataloader pin memory. | Only affects the test dataloader. |
| `--tta` | Enable test-time augmentation. | Uses `tta_model` and `tta_pipeline` when present; otherwise falls back to flip TTA. |

Examples:

```bash
# CPU-only evaluation
CUDA_VISIBLE_DEVICES=-1 mim test mmpretrain path/to/config.py --checkpoint path/to/ckpt.pth --gpus 0

# Dump predictions
mim test mmpretrain path/to/config.py --checkpoint path/to/ckpt.pth --out results.pkl

# Dump metrics instead of predictions
mim test mmpretrain path/to/config.py --checkpoint path/to/ckpt.pth --out metrics.json --out-item metrics

# TTA evaluation with visualization output
mim test mmpretrain path/to/config.py --checkpoint path/to/ckpt.pth --tta --show-dir vis_results
```

## Distributed launch patterns

### Multi-GPU single machine

```bash
mim train mmpretrain path/to/config.py --gpus 4 --launcher pytorch --port 29666 [TRAIN_ARGS]
mim test mmpretrain path/to/config.py --checkpoint path/to/ckpt.pth --gpus 4 --launcher pytorch --port 29666 [TEST_ARGS]
```

Use `CUDA_VISIBLE_DEVICES` to bind a job to a device subset. Use a different `--port` for concurrent distributed jobs.

### Multiple machines on one network

Each node must agree on `NNODES`, `MASTER_ADDR`, and `PORT`, while `NODE_RANK` changes per node. Use the same MIM command on each node with the proper environment:

```bash
NNODES=2 NODE_RANK=0 MASTER_ADDR=$MASTER_ADDR mim train mmpretrain path/to/config.py --gpus 8 --launcher pytorch --port $MASTER_PORT
NNODES=2 NODE_RANK=1 MASTER_ADDR=$MASTER_ADDR mim train mmpretrain path/to/config.py --gpus 8 --launcher pytorch --port $MASTER_PORT
```

If a job hangs, check that the port is free, every node sees the same master address, and the backend package matches the GPU/driver stack.

## Slurm launch patterns

```bash
mim train mmpretrain path/to/config.py --launcher slurm --partition PARTITION --gpus 8 --gpus-per-node 8 --cpus-per-task 5 --work-dir work_dirs/run1 [TRAIN_ARGS]
mim test mmpretrain path/to/config.py --checkpoint path/to/ckpt.pth --launcher slurm --partition PARTITION --gpus 8 --gpus-per-node 8 --cpus-per-task 5 [TEST_ARGS]
```

Slurm controls:

| Option | Meaning |
| --- | --- |
| `--partition` | Slurm partition. |
| `--gpus` | Total number of GPUs/tasks to request. |
| `--gpus-per-node` | GPUs allocated per node. |
| `--cpus-per-task` | CPU cores allocated per task. |
| `--srun-args` | Additional scheduler-specific `srun` arguments. |

## K-fold cross validation

Package-dispatched pattern:

```bash
mim run mmpretrain kfold-cross-valid path/to/config.py --num-splits 5
mim run mmpretrain kfold-cross-valid path/to/config.py --num-splits 5 --fold 2
mim run mmpretrain kfold-cross-valid path/to/config.py --num-splits 5 --resume
```

K-fold notes:

- `--num-splits` is required.
- `--fold` runs a single fold instead of all remaining folds.
- `--resume` reads fold state and the latest checkpoint from the K-fold work directory.
- The helper wraps the original training dataset in `KFoldDataset` and reuses validation/test pipelines.
- If MIM cannot locate the K-fold command in the installed package, write an explicit config using `KFoldDataset` and launch it with `mim train mmpretrain`.

## Bundled command helper

Examples for the safe command printer:

```bash
python ../scripts/build_train_test_command.py train path/to/config.py --cpu --amp
python ../scripts/build_train_test_command.py test path/to/config.py path/to/ckpt.pth --tta --out results.pkl
python ../scripts/build_train_test_command.py dist-train path/to/config.py 8 --port 29666
python ../scripts/build_train_test_command.py slurm-test PARTITION JOB_NAME path/to/config.py path/to/ckpt.pth
```

The helper prints a command only; it does not launch training, testing, distributed workers, or Slurm jobs.
