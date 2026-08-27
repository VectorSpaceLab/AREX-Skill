# LaneNet Training Workflows

This reference covers LaneNet training only. Generate TFRecords in `../data-preparation/`, and use `../inference-evaluation/` for checkpoint-backed testing.

## Environment and run directory

LaneNet source imports are repo-root-relative, and the shipped config contains `REPO_ROOT_PATH` placeholders. The bundled training wrapper resolves those placeholders for you, but the safest operating pattern is still to run from the repository root or pass `--repo_root` explicitly.

Verified training facts for this repo skill:

- TensorFlow 1.15 with CUDA is the validated training environment.
- The default backbone is `bisenetv2`; `vgg` is supported by the front-end dispatch map.
- Default multi-GPU config is enabled with devices `['0', '1']`.
- Default batch size is `32`, warm-up is enabled, and poly decay is used after warm-up.
- Training logs, TensorBoard summaries, and snapshots all use the front-end name in the output subdirectory, such as `bisenetv2_lanenet`.

## Train from scratch

Use this flow when starting a new model from prepared TFRecords and no checkpoint restore.

```bash
python <skill-dir>/scripts/train_lanenet_tusimple.py \
  --repo_root <repo-root> \
  --run
```

The wrapper is dry-run by default. Add `--run` only when you really want to launch training.

Helpful config overrides:

| Override | Meaning |
| --- | --- |
| `MODEL.FRONT_END=bisenetv2` | Default backbone. |
| `MODEL.FRONT_END=vgg` | Switch to the VGG16 FCN front end. Use only with a matching checkpoint or from-scratch run. |
| `TRAIN.MULTI_GPU.ENABLE=False` | Force single-GPU training. |
| `TRAIN.BATCH_SIZE=4` | Smaller batch for smoke runs or limited memory. |
| `TRAIN.EPOCH_NUMS=2` | Short smoke run. |
| `TRAIN.SNAPSHOT_EPOCH=1` | Save a checkpoint every epoch. |
| `TRAIN.COMPUTE_MIOU.ENABLE=False` | Reduce overhead for smoke checks. |

Keep `TRAIN.WARM_UP.ENABLE=True` for normal and smoke runs. The upstream trainer still traces its warm-up branch during graph construction, so disabling warm-up can trigger an `AttributeError` before training starts. If you need a shorter run, lower `TRAIN.EPOCH_NUMS` and `TRAIN.BATCH_SIZE` instead of disabling warm-up.

A successful from-scratch run should log the loss components, create a TensorBoard directory, and eventually write `.ckpt-*` files under the model-save directory.

## Restore from a snapshot

Use this flow when resuming from a prior LaneNet checkpoint.

```bash
python <skill-dir>/scripts/train_lanenet_tusimple.py \
  --repo_root <repo-root> \
  --run \
  --set TRAIN.RESTORE_FROM_SNAPSHOT.ENABLE=True \
  --set TRAIN.RESTORE_FROM_SNAPSHOT.SNAPSHOT_PATH=path/to/model.ckpt-12345
```

Guidance:

- Pass the checkpoint base path, not just `.index` or `.data-*` shards.
- The trainer restores the moving-average variables and then resumes from the inferred global step.
- Keep `MODEL.FRONT_END` and `MODEL.EMBEDDING_FEATS_DIMS` consistent with the checkpoint.
- If the restore path is missing or incompatible, the source trainer falls back to scratch; the bundled wrapper surfaces that mismatch earlier.

## Single-GPU training

Use single GPU when debugging, when only one device is visible, or when the batch size is too small for multi-GPU sharding.

```bash
python <skill-dir>/scripts/train_lanenet_tusimple.py \
  --repo_root <repo-root> \
  --run \
  --set TRAIN.MULTI_GPU.ENABLE=False \
  --set TRAIN.BATCH_SIZE=4 \
  --set TRAIN.VAL_BATCH_SIZE=2
```

Notes:

- The single-GPU trainer only needs the train TFRecord set.
- It logs `total_loss`, `binary_seg_loss`, `discriminative_loss`, and `miou` when enabled.
- It saves snapshots named with training loss or mIoU, depending on `TRAIN.COMPUTE_MIOU.ENABLE`.

## Multi-GPU training

Use multi-GPU when the visible CUDA devices match the config and the batch size is divisible by the device count.

```bash
python <skill-dir>/scripts/train_lanenet_tusimple.py \
  --repo_root <repo-root> \
  --run \
  --set TRAIN.MULTI_GPU.ENABLE=True \
  --set "TRAIN.MULTI_GPU.GPU_DEVICES=['0','1']" \
  --set TRAIN.BATCH_SIZE=32 \
  --set TRAIN.VAL_BATCH_SIZE=4
```

Notes:

- The multi-GPU trainer loads both train and validation TFRecords.
- `TRAIN.MULTI_GPU.CHIEF_DEVICE_INDEX` selects the tower that contributes the main summaries.
- The per-GPU batch size is computed by integer division, so a batch size smaller than the GPU count will fail and a non-divisible batch size will be rounded down.
- Validation summaries appear only when the validation TFRecord set produces at least one full batch.

## Tiny smoke adjustments

Use these adjustments when validating graph construction or a tiny prepared dataset.

```bash
python <skill-dir>/scripts/train_lanenet_tusimple.py \
  --repo_root <repo-root> \
  --run \
  --set TRAIN.MULTI_GPU.ENABLE=False \
  --set TRAIN.BATCH_SIZE=2 \
  --set TRAIN.VAL_BATCH_SIZE=2 \
  --set TRAIN.EPOCH_NUMS=2 \
  --set TRAIN.SNAPSHOT_EPOCH=1 \
  --set TRAIN.COMPUTE_MIOU.ENABLE=False \
  --set TRAIN.WARM_UP.ENABLE=True
```

Keep warm-up enabled for these smoke runs. If you need a shorter run, lower `TRAIN.EPOCH_NUMS` or `TRAIN.BATCH_SIZE` instead of disabling warm-up. Also make the batch size strictly smaller than the number of training records. The source training loop iterates over `range(1, steps_per_epoch)`, so `steps_per_epoch <= 1` produces no training step and no checkpoint.

## What to look for in a healthy run

- Training logs show `Train loss` and, when enabled, `Train miou`.
- Multi-GPU logs also show validation loss and validation mIoU.
- Snapshot files appear under `model/tusimple/<front_end>_lanenet/`.
- TensorBoard event files and `model_train_config.json` appear under `tboard/tusimple/<front_end>_lanenet/`.
- The log file is created under `log/` and records the same epoch summaries.
