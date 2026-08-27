# Training Workflows

## Purpose

Read this when you need to turn a repo config into a safe training command.

## Verified entry point

- `train.py` is the main training script.
- It reads a config file, merges explicit CLI overrides, and launches the training loop.
- Distributed training uses `torch.distributed` with NCCL when `WORLD_SIZE > 1`.

## Single-GPU pattern

```bash
python train.py configs/culane.py --data_root <CULANE_ROOT> --log_path <LOG_DIR>
python train.py configs/tusimple.py --data_root <TUSIMPLE_ROOT> --log_path <LOG_DIR>
```

Add only the overrides the user needs, such as `--batch_size`, `--backbone`, `--resume`, `--finetune`, or `--use_aux`.

## Multi-GPU pattern

The repo's launcher is a shell snippet that exports visible devices and `NGPUS`, then runs `python -m torch.distributed.launch` against `train.py`.

A safer pattern is to parameterize those values in a small wrapper script and keep the log path outside the repository.

## What the training loop uses

- `get_train_loader(...)` for the dataset and row-anchor selection.
- `parsingNet(...)` for the model.
- `get_optimizer(...)` for Adam or SGD.
- `get_scheduler(...)` for multi-step or cosine scheduling.
- `get_loss_dict(...)` for the classification, relation, auxiliary, and relation-distance losses.
- `get_metric_dict(...)` for top-k and optional mIoU metrics.
- `save_model(...)` to save `ep%03d.pth` checkpoints.
- `get_work_dir(cfg)` to build the logging directory under `log_path`.

## Checkpoint lifecycle

- `finetune` is loaded as backbone-only state when present.
- `resume` expects a checkpoint that already contains both `model` and `optimizer` state.
- The resume logic derives the next epoch from the checkpoint filename, so keep the `ep%03d.pth` naming convention.

## Logging and backup

- The repo writes TensorBoard logs under the configured work directory.
- `cp_projects(True, work_dir)` copies the working tree into the log directory.
- Keep the log directory outside the repository tree to avoid copying large data or generated artifacts.

## Backbone and shape alignment

- The repo accepts ResNet/ResNeXt/Wide-ResNet variants listed in `train.py` and `model/backbone.py`.
- `griding_num`, `num_lanes`, and `use_aux` must match the dataset family and checkpoint.
- TuSimple and CULane use different row-anchor counts and class dimensions.
