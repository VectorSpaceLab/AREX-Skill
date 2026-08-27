# Training workflows

## Entry points

### `train.py`

Core arguments:

| Argument | Meaning | Notes |
|---|---|---|
| `--resume PATH` | Load a checkpoint and continue training | If the file exists, the checkpoint state is loaded with prefix cleanup and the epoch counter starts from the number in the filename + 1. |
| `--epochs N` | Final absolute epoch number | This is not "extra epochs". If you resume from `epoch_244.pth` and want 50 more epochs, set `--epochs 294`. |
| `--ckpt_dir PATH` | Checkpoint/log output directory | `train.py` creates it and writes `log.txt` plus `epoch_*.pth`. |
| `--dist True\|False` | Use native DDP | `True` expects `torchrun`/NCCL and a visible multi-GPU setup. |
| `--use_accelerate` | Use Accelerate | Intended for multi-GPU or mixed-precision runs. When enabled, the script sets `--dist` off internally. |

Behavior notes:

- The model starts with backbone pretrained weights unless a valid `--resume` file is loaded.
- Checkpoints are saved only in the configured save window: `epoch >= args.epochs - config.save_last` and `epoch % config.save_step == 0`.
- `config.save_last` and `config.save_step` are populated from `train.sh` when that launcher is visible from the current repo root.
- The default config uses `torch.compile` and bf16 mixed precision. If compile-related failures occur, diagnose with a simpler PyTorch build or temporarily disable compile in the config.

### `train.sh`

The shell launcher picks the schedule from `Config.task` and then chooses a run directory under `ckpts/${method}`.

| Task | Epochs | `val_last` | `step` |
|---|---:|---:|---:|
| `DIS5K` | 500 | 50 | 5 |
| `COD` | 150 | 50 | 5 |
| `HRSOD` | 150 | 50 | 5 |
| `General` | 200 | 50 | 5 |
| `General-2K` | 250 | 30 | 2 |
| `Matting` | 150 | 50 | 5 |

Other launch details:

- `train.sh` reads the task from `config.py` and expects to be run from the repo root.
- GPU IDs are comma-separated, such as `0,1,2,3`.
- The script uses `CUDA_VISIBLE_DEVICES=...` and switches between single-GPU Python and multi-GPU `torchrun` automatically.
- `resume_weights_path` is a placeholder string in the source launcher and must be edited before use.

### `train_test.sh`

`train_test.sh` is a convenience wrapper that runs:

1. `bash train.sh ...`
2. `bash test.sh ...`
3. `hostname`

Use it when you want a single command for train → inference → evaluation.

## Resume semantics

- `train.py` extracts the epoch number from the checkpoint filename suffix `epoch_<N>.pth`.
- The training loop resumes from `N + 1`.
- The README example is the intended rule of thumb: if you resume from `BiRefNet-general-epoch_244.pth` and want 50 more epochs, set `--epochs 294`.
- If the `--resume` path does not exist, the script logs that no checkpoint was found and starts a fresh run.

## Fine-tuning schedule

`Config.finetune_last_epochs` switches the loss mix in the last part of training:

| Task family | Last-phase offset | Effect |
|---|---:|---|
| `DIS5K` | `-40` | Final epochs rebalance the segmentation losses. |
| `COD`, `HRSOD`, `General`, `General-2K` | `-20` | Final epochs reduce BCE and slightly shift IoU/MAE weighting. |
| `Matting` | `-10` | Final epochs emphasize matting-style losses. |

Inside that last window, `train.py` adjusts the active loss weights before each batch. This is why the task schedule is not only about checkpoint cadence; it also changes optimization behavior near the end of a run.

## Memory and precision notes

- The default config assumes high-memory training and bf16 support.
- README memory notes report roughly 36.5GB+ for single-GPU training on the standard setup, while two-GPU batch-size-2 runs with compile/BF16 are lower.
- If you hit OOM, lower `Config.batch_size`, use more GPUs, or disable compile temporarily for diagnosis.

## Safe operating advice

- Keep launch commands explicit when you are not sitting in the repo root; many defaults are relative paths.
- Prefer a valid checkpoint path for `--resume` instead of relying on `train.sh` placeholders.
- For task or dataset changes, confirm the dataset and config routing in the configuration sub-skill before editing training schedules.
