# Training CLI and API Reference

This reference covers `nnUNetv2_train` and the equivalent `run_training(...)` API after experiment planning and preprocessing already exist.

## CLI Shape

```bash
nnUNetv2_train DATASET_NAME_OR_ID CONFIGURATION FOLD [options]
```

Arguments:

- `DATASET_NAME_OR_ID`: either an integer dataset ID or a full dataset name such as `Dataset001_Example`.
- `CONFIGURATION`: planned configuration to train, commonly `2d`, `3d_fullres`, `3d_lowres`, or `3d_cascade_fullres`.
- `FOLD`: integer fold such as `0` through `4`, or `all` for training on all available training cases.

The dataset must have a preprocessed dataset folder containing `dataset.json` and the selected plans file, for example `nnUNetPlans.json`.

## Core Options

| Option | Use |
| --- | --- |
| `-tr TRAINER` | Select trainer class by name. Default: `nnUNetTrainer`. |
| `-p PLANS` | Select plans identifier. Default: `nnUNetPlans`. |
| `--npz` | Export validation softmax probabilities as `.npz`; needed for automatic best-configuration/ensemble workflows. |
| `--c` | Continue training from a checkpoint in the fold output folder. |
| `--val` | Only run validation. Requires completed training. Useful to regenerate validation outputs, including `--npz`. |
| `--val_best` | Validate `checkpoint_best.pth` instead of `checkpoint_final.pth`; cannot be combined with `--disable_checkpointing`. |
| `--disable_checkpointing` | Disable checkpoint writes for short experiments; do not use for long runs that must resume. |
| `-pretrained_weights PATH` | Initialize compatible network weights before training. Cannot be combined with continuing training. |
| `-device cuda|cpu|mps` | Select device type. Default: `cuda`. Use `CUDA_VISIBLE_DEVICES` for GPU IDs. |
| `-num_gpus N` | Use distributed data parallel training with `N` CUDA GPUs for one fold/configuration. |

Invalid combinations:

- `--c` and `--val` are mutually exclusive.
- `--c` and `-pretrained_weights` are mutually exclusive.
- `--val_best` is incompatible with `--disable_checkpointing`.
- `-num_gpus` greater than `1` requires `-device cuda`.

## Python API Mapping

The CLI dispatches to:

```python
run_training(
    dataset_name_or_id,
    configuration,
    fold,
    trainer_class_name="nnUNetTrainer",
    plans_identifier="nnUNetPlans",
    pretrained_weights=None,
    num_gpus=1,
    export_validation_probabilities=False,
    continue_training=False,
    only_run_validation=False,
    disable_checkpointing=False,
    val_with_best=False,
    device=torch.device("cuda"),
)
```

Use the CLI for normal training. Use the Python API only when embedding nnU-Net inside a larger Python orchestration layer and after importing a working nnU-Net installation.

## Configuration and Fold Patterns

Train one fold:

```bash
nnUNetv2_train Dataset001_Example 3d_fullres 0 --npz
```

Train five-fold cross-validation:

```bash
for fold in 0 1 2 3 4; do
  nnUNetv2_train Dataset001_Example 3d_fullres "$fold" --npz
done
```

Train on all training cases:

```bash
nnUNetv2_train Dataset001_Example 3d_fullres all
```

Use `all` for final training or pretraining when validation-based model selection is not the goal. Use separate folds when cross-validation, model selection, or ensembling are needed.

## Cascade Configuration

`3d_cascade_fullres` depends on `3d_lowres` outputs. Train low resolution first:

```bash
nnUNetv2_train Dataset001_Example 3d_lowres 0 --npz
nnUNetv2_train Dataset001_Example 3d_cascade_fullres 0 --npz
```

Repeat this ordering for every fold. If `3d_lowres` was not planned for the dataset, do not attempt the cascade.

## Devices and GPU Selection

Single CUDA GPU:

```bash
CUDA_VISIBLE_DEVICES=0 nnUNetv2_train Dataset001_Example 3d_fullres 0 --npz
```

Multiple independent folds on multiple GPUs:

```bash
CUDA_VISIBLE_DEVICES=0 nnUNetv2_train Dataset001_Example 3d_fullres 0 --npz
CUDA_VISIBLE_DEVICES=1 nnUNetv2_train Dataset001_Example 3d_fullres 1 --npz
```

Single fold with DDP:

```bash
CUDA_VISIBLE_DEVICES=0,1 nnUNetv2_train Dataset001_Example 3d_fullres 0 --npz -num_gpus 2
```

Prefer one fold per GPU when the user wants to finish cross-validation quickly and has enough folds/configurations to parallelize. Use `-num_gpus` when one run needs more memory/throughput or the training plan explicitly calls for DDP. DDP uses CUDA process groups and is not implemented for CPU or MPS.

CPU and MPS are selectable with `-device`, but they are typically much slower than CUDA and may not be appropriate for production training:

```bash
nnUNetv2_train Dataset001_Example 2d 0 -device cpu
nnUNetv2_train Dataset001_Example 2d 0 -device mps
```

## Trainer and Plans Selection

Select a trainer by class name with `-tr`:

```bash
nnUNetv2_train Dataset001_Example 3d_fullres 0 -tr nnUNetTrainer_250epochs --npz
```

Bundled trainer variants include benchmarking, loss, optimizer, learning-rate, data-augmentation, architecture, sampling, and training-length variants. The class must be discoverable by nnU-Net's trainer lookup. Implementing new trainer classes belongs in `customization-extension`; this reference only covers selecting existing or installed trainers.

Select a non-default plans identifier with `-p`:

```bash
nnUNetv2_train Dataset001_Example 3d_fullres 0 -p CustomPlans --npz
```

The matching plans JSON must exist in the preprocessed dataset folder.

## Checkpoints and Output Layout

Training writes to:

```text
nnUNet_results/DatasetXXX_Name/TRAINER__PLANS__CONFIGURATION/fold_X/
```

Common artifacts:

- `checkpoint_latest.pth`: checkpoint used for continuing an interrupted run when present.
- `checkpoint_final.pth`: final checkpoint after training completes.
- `checkpoint_best.pth`: best checkpoint according to validation tracking.
- `training_log_*.txt`: console-style training log.
- `progress.png`: local training curves generated from logged metrics.
- `debug.json`: trainer, plans, and runtime debug metadata.
- `validation/summary.json`: validation metrics summary.
- `validation/*.npz`: validation probabilities when `--npz` was enabled.

When `--c` is used, nnU-Net tries to resume from `checkpoint_final.pth`, then `checkpoint_latest.pth`, then `checkpoint_best.pth`; if none exists it warns and starts a new training run.

## Logging

Local logging is always enabled and drives `progress.png`. Per-epoch values include foreground Dice summaries, per-class/region Dice, training and validation losses, learning rates, and epoch timestamps. Logging state is saved and restored with checkpoints so resumed curves remain continuous.

Optional Weights & Biases logging can be enabled with environment variables before training:

```bash
export nnUNet_wandb_enabled=1
export nnUNet_wandb_project=nnunet
export nnUNet_wandb_mode=online
nnUNetv2_train Dataset001_Example 3d_fullres 0 --npz
```

`nnUNet_wandb_mode=offline` is also supported. When resuming, W&B resume metadata in the fold output is reused where available.
