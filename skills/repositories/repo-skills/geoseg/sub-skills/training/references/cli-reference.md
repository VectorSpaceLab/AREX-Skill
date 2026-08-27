# Training CLI and config reference

## Native CLI

The training script exposes one required argument:

```text
usage: train_supervision.py [-h] -c CONFIG_PATH

-c CONFIG_PATH, --config_path CONFIG_PATH  Path to the config.
```

Canonical command templates:

```bash
export GEOSEG_SKILL=/path/to/this/skill

# Static, non-executing validation; the config is supplied from the user's checkout.
python "$GEOSEG_SKILL/sub-skills/training/scripts/check_training_config.py" \
  /path/to/GeoSeg/config/uavid/unetformer.py

# Native training through the shared wrapper (expensive; requires data and weights)
# --repo-root must be the user's GeoSeg checkout; keep the config argument user-provided.
python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" \
  --repo-root /path/to/GeoSeg \
  train_supervision.py -c config/uavid/unetformer.py

# Native argument parser smoke check after integration
python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" \
  --repo-root /path/to/GeoSeg \
  train_supervision.py --help
```

The config path must end in `.py`. `tools.cfg.py2dict` rejects a non-Python
suffix, a missing file, or a filename stem containing a dot. Since config
loading imports the module and executes its top-level code, use a path whose
parent can be imported and avoid relying on the static validator to prove
runtime imports.

There are no native command-line switches for epochs, batch sizes, devices,
checkpoint paths, monitoring, or output directories. Set those in the Python
config. Do not pass undocumented flags expecting them to override config
values.

## Required config contract

The following names are consumed directly by `train_supervision.py` or by the
`ModelCheckpoint`/logger construction and should be present in every training
config:

| Name | Expected role |
| --- | --- |
| `net` | `torch.nn.Module` segmentation network |
| `loss` | Callable loss accepting model output and integer mask |
| `train_loader` | Loader yielding `img` and `gt_semantic_seg` |
| `val_loader` | Validation loader yielding the same keys |
| `classes` | Ordered class names for per-class IoU display |
| `num_classes` | Positive number of confusion-matrix/output classes |
| `use_aux_loss` | Boolean matching training output handling |
| `gpus` | Lightning `devices` value, commonly `'auto'` |
| `max_epoch` | Positive maximum epoch count |
| `check_val_every_n_epoch` | Positive validation interval |
| `monitor` | `val_mIoU`, `val_F1`, or `val_OA` |
| `monitor_mode` | Usually `'max'`; passed to `ModelCheckpoint.mode` |
| `save_top_k` | Checkpoint count; `-1` means keep all in Lightning |
| `save_last` | Boolean passed to `ModelCheckpoint` |
| `weights_path` | Checkpoint directory |
| `weights_name` | Checkpoint filename template |
| `log_name` | CSV logger name and metric dataset token |
| `pretrained_ckpt_path` | Checkpoint initialization path or `None` |
| `resume_ckpt_path` | Lightning resume path or `None` |
| `optimizer` | Instantiated optimizer |
| `lr_scheduler` | Instantiated scheduler |

`ignore_index` is not read by the trainer itself, but the configured loss and
mask preparation normally depend on it and the validator checks for it as a
strong warning. Dataset configs also normally define `train_batch_size`,
`val_batch_size`, `lr`, `weight_decay`, `backbone_lr`, and
`backbone_weight_decay`; these are useful provenance fields even though the
trainer receives already-built objects.

`test_dataset` and `test_weights_name` occur in many configs but are not used
by `train_supervision.py`. Do not infer that defining them changes training.
Likewise, `accumulate_n` occurs in the Vaihingen DCSwin config but is not read
by this script.

## Checked-in configuration families

The following are representative config paths, not guarantees that external
data or weights are present:

```text
config/loveda/dcswin.py
config/loveda/unetformer.py
config/potsdam/dcswin.py
config/potsdam/ftunetformer.py
config/potsdam/unetformer.py
config/uavid/unetformer.py
config/vaihingen/dcswin.py
config/vaihingen/ftunetformer.py
config/vaihingen/unetformer.py
```

Typical model/loss patterns:

- `UNetFormer`: `use_aux_loss=True`, `UnetFormerLoss(ignore_index=...)`; its
  model returns `(main, auxiliary)` while training and only the main tensor in
  evaluation mode.
- `DCSwin` and `FTUNetFormer`: usually `use_aux_loss=False` and a weighted
  `JointLoss` of smoothed cross-entropy plus Dice loss.
- DCSwin LoveDA may request a backbone file such as
  `pretrain_weights/stseg_small.pth` during config import.
- FTUNetFormer's factory can load a backbone checkpoint during config import
  when `pretrained=True` and `weight_path` is not `None`.

PyramidMamba is present in the source tree but its optional `mamba_ssm`
dependency was not verified. Treat a PyramidMamba config as blocked until its
backend is explicitly installed and smoke-tested.

## Data layout contract for training

Training configs refer to processed datasets. The dataset classes enumerate
image and mask directories at construction and assert matching file counts.
Use the data-preparation workflow to create them; training does not split,
convert, or repair data.

| Dataset | Common training root | Required subdirectories / details | Ignore value |
| --- | --- | --- | --- |
| LoveDA | `data/LoveDA/Train` or `data/LoveDA/train_val` | Under both `Urban` and `Rural`: `images_png` and `masks_png_convert`; validation module defaults to `data/LoveDA/Val` | `len(CLASSES)` (7) |
| Potsdam | `data/potsdam/train` | `images_1024`, `masks_1024`; validation/test commonly use `data/potsdam/test` | `len(CLASSES)` (6) |
| Vaihingen | `data/vaihingen/train` | `images_1024`, `masks_1024`; validation/test commonly use `data/vaihingen/test` | `len(CLASSES)` (6) |
| UAVid | `data/uavid/train_val` or `data/uavid/train` | `images`, `masks`; validation commonly uses `data/uavid/val` | `255` |

The class tuples evidenced in the dataset modules are:

```text
LoveDA:    background, building, road, water, barren, forest, agricultural
Potsdam:   ImSurf, Building, LowVeg, Tree, Car, Clutter
Vaihingen: ImSurf, Building, LowVeg, Tree, Car, Clutter
UAVid:     Building, Road, Tree, LowVeg, Moving_Car, Static_Car, Human, Clutter
```

## Checkpoint and output fields

The source creates a `ModelCheckpoint` with `dirpath=weights_path` and
`filename=weights_name`, and a `CSVLogger` rooted at `lightning_logs` with
`name=log_name`. Use project-relative paths in configs when portability is
wanted. Verify that the parent output directories are writable before a run.

Checkpoint mode should generally be:

```python
monitor = 'val_mIoU'  # or 'val_F1' / 'val_OA'
monitor_mode = 'max'
save_top_k = 1
save_last = True
```

To resume the last state:

```python
pretrained_ckpt_path = None
resume_ckpt_path = 'model_weights/<dataset>/<checkpoint>.ckpt'
```

To initialize from a checkpoint without restoring its optimizer/scheduler
state:

```python
pretrained_ckpt_path = 'path/to/initial.ckpt'
resume_ckpt_path = None
```

Keep both `None` for a fresh run. Confirm the checkpoint's architecture,
class count, optimizer state compatibility, and monitor policy before use.
