# Training workflows

This reference describes the lifecycle implemented by `train_supervision.py`.
It is an operating guide, not a replacement trainer. Full execution is
skip-expensive until data, optional weights, GPU/backend, and output storage
are verified.

## 1. Preflight without importing the config

Identify the dataset/model pair in the user's GeoSeg checkout. Run the static
validator before any command that imports a config:

```bash
python skills/disco/geoseg/sub-skills/training/scripts/check_training_config.py \
  config/vaihingen/unetformer.py
```

The validator checks syntax, required assignment names, literal control
values, checkpoint intent, and the monitor name. It cannot prove that a
config's top-level imports work, because the repository's Python configs
construct networks, optimizers, loaders, and datasets while being imported.

Next check the external prerequisites manually:

- dataset directories and paired image/mask files exist;
- preprocessing has produced the directory names expected by the selected
  dataset class;
- any backbone `weight_path` or checkpoint path exists and is readable;
- `model_weights/<dataset>/...` and `lightning_logs/...` are writable;
- the effective Python environment has the source's importable dependencies;
- a CUDA device is visible if the intended run is GPU-backed.

The checkout has no packaging metadata. Use the shared bundled wrapper for
operational commands and set `--repo-root` to the user's GeoSeg checkout; do
not invoke checkout entrypoint files directly or expect `pip install .` to
provide a package.

## 2. Understand config import and object construction

`tools.cfg.py2cfg` requires a `.py` file, resolves it to an absolute path, adds
its parent to `sys.path`, imports the module by stem, and wraps all non-dunder
module values in an `addict.Dict`. This is executable Python configuration,
not a declarative file. Imports and top-level expressions therefore happen
before `Supervision_Train` is built.

The config must provide the objects consumed by the trainer:

- `net`: an `nn.Module` returning per-pixel logits; during training an
  auxiliary model may return a `(main, auxiliary)` pair;
- `loss`: callable on `(prediction, mask)`;
- `train_loader` and `val_loader`: loaders whose batches contain `img` and
  `gt_semantic_seg`;
- `num_classes`, `classes`, and `use_aux_loss`;
- optimizer and scheduler objects in `optimizer` and `lr_scheduler`;
- checkpoint, logging, device, and epoch fields listed in
  [cli-reference.md](cli-reference.md).

For a real import, expect dataset constructors to call `os.listdir` and fail
if the layout is absent. In particular, importing
`geoseg.datasets.loveda_dataset` instantiates `loveda_val_dataset` at module
scope, so every LoveDA config needs the Val Urban/Rural image and converted
mask directories even before a trainer is created.

## 3. Understand `Supervision_Train`

The module stores `config.net` and `config.loss`, creates two `Evaluator`
instances with `num_class=config.num_classes`, and exposes the network through
`forward`. `configure_optimizers` returns the config optimizer and scheduler;
`train_dataloader` and `val_dataloader` return the already-built config
loaders. There is no data-module abstraction and no automatic batch-size
scaling.

Training does the following for each batch:

1. reads `batch['img']` and `batch['gt_semantic_seg']`;
2. computes `prediction = self.net(img)`;
3. computes `loss = self.loss(prediction, mask)`;
4. converts logits to class IDs with softmax/argmax for the confusion matrix;
5. if `use_aux_loss` is true, uses `prediction[0]` for the training metric,
   otherwise uses `prediction` directly;
6. returns `{'loss': loss}`.

`UnetFormerLoss` itself adds the auxiliary loss when the module is in training
mode and the prediction has length two. Thus `use_aux_loss` must agree with
the selected model's training-time output contract. It is not a generic switch
that can make an arbitrary model return auxiliary logits. In validation,
Lightning switches the model to evaluation mode; UNetFormer then returns its
main tensor, and the script applies softmax/argmax directly. A custom model
that returns a tuple in evaluation must be adapted before using this trainer.

At epoch end the script prints a dictionary for train or val containing
`mIoU`, `F1`, and `OA`, prints a per-class IoU dictionary, resets the evaluator,
and logs `train_mIoU`, `train_F1`, `train_OA` or `val_mIoU`, `val_F1`, and
`val_OA` to the progress bar/logger.

## 4. Select the checkpoint intent

### Fresh run

Set both `pretrained_ckpt_path` and `resume_ckpt_path` to `None`. If a model
factory itself has `pretrained=True`, any backbone weight file required by the
factory is a separate prerequisite and is loaded during config import.

### Initialize from a pretrained checkpoint

Set `pretrained_ckpt_path` to a readable Lightning checkpoint and keep
`resume_ckpt_path=None`:

```python
pretrained_ckpt_path = 'path/to/pretrained.ckpt'
resume_ckpt_path = None
```

The script constructs `Supervision_Train(config)` and then replaces it with
`Supervision_Train.load_from_checkpoint(..., config=config)`. This is a model
initialization path. It does not mean “continue the old optimizer/scheduler
run”; make sure the new config's class count, architecture, loss, and loaders
are compatible with the checkpoint.

### Resume an interrupted run

Set `resume_ckpt_path` to the checkpoint produced by Lightning and keep
`pretrained_ckpt_path=None`:

```python
pretrained_ckpt_path = None
resume_ckpt_path = 'path/to/weights/last.ckpt'
```

The trainer receives `ckpt_path=config.resume_ckpt_path` in `trainer.fit`, so
Lightning restores the model and training state (epoch, optimizer,
scheduler, and callback state when present). Keep the architecture, optimizer
shape, class count, and scheduler compatible. If intentionally changing those,
start from a fresh run or use the pretrained initialization path and document
what is being discarded.

Do not set both paths to different checkpoints as a shortcut. The source first
loads `pretrained_ckpt_path` and then asks `fit` to restore
`resume_ckpt_path`; this creates ambiguous state precedence and is not a
supported “pretrain then resume” protocol.

## 5. Configure monitoring and saving

`main` creates:

```python
ModelCheckpoint(
    save_top_k=config.save_top_k,
    monitor=config.monitor,
    save_last=config.save_last,
    mode=config.monitor_mode,
    dirpath=config.weights_path,
    filename=config.weights_name,
)
```

Use exactly one of `val_mIoU`, `val_F1`, or `val_OA` for `monitor`. The
repository configs use `monitor_mode='max'` because all three are higher-is-
better metrics. With `save_top_k=1`, the best monitored checkpoint is kept;
with `save_last=True`, Lightning also writes a last checkpoint. The source's
`test_weights_name` is not read by this training script; evaluation scripts
may use it separately.

`check_val_every_n_epoch` controls when validation and therefore monitored
metrics occur. If validation is infrequent, checkpoint ranking is infrequent
as well. A monitor mismatch commonly surfaces as a missing monitored-key
error or no useful best checkpoint; fix the config before retrying.

The CSV logger writes under `lightning_logs` with `name=config.log_name`.
`log_name` is also used for metric averaging behavior, so do not casually
rename a dataset token in it (see the next section).

## 6. Dataset, loader, augmentation, and loss alignment

The checked-in configs use `DataLoader` with `batch_size`, `num_workers=4`,
`pin_memory=True`, shuffled/drop-last training, and non-shuffled/non-dropping
validation. The dataset transforms normalize images and, for the ISPRS
configs, perform random scale plus `SmartCropV1`; LoveDA and UAVid use their
own transform definitions. Do not change crop size, batch size, or mosaic
ratio without reconsidering GPU memory and mask dimensions.

Canonical config families include:

- LoveDA: `data/LoveDA/Train` or `data/LoveDA/train_val` for training and a
  module-created `data/LoveDA/Val` validation dataset. Images and converted
  masks live under `Urban` and `Rural`; typical subdirectories are
  `images_png` and `masks_png_convert`.
- Potsdam: processed `data/potsdam/train` and validation/test roots with
  `images_1024` and `masks_1024`.
- Vaihingen: processed `data/vaihingen/train` and validation/test roots with
  `images_1024` and `masks_1024`.
- UAVid: processed `data/uavid/train_val` or `train` and `data/uavid/val`,
  with `images` and `masks`.

The config's `ignore_index` is normally `len(CLASSES)` for LoveDA, Potsdam,
and Vaihingen; UAVid uses `255`. It must be passed consistently to losses and
remain outside the valid class range. Dataset preparation owns conversion and
splitting; training only consumes the resulting layout.

Common losses are `JointLoss(SoftCrossEntropyLoss(...), DiceLoss(...))` for
DCSwin/FTUNetFormer and `UnetFormerLoss(ignore_index=...)` for UNetFormer.
The loss must accept the model's output shape and the mask's integer dtype.
Optimizer setup commonly uses `process_model_params` with a lower learning
rate for `backbone.*`, AdamW, the repository's `Lookahead`, and a cosine
scheduler. These are instantiated at config import and are restored from a
resume checkpoint when compatible.

## 7. Interpret metrics correctly

`tools.metric.Evaluator` accumulates a `num_classes × num_classes` confusion
matrix. Ground-truth pixels are counted only when `0 <= gt < num_classes`, so
an ignore label of `255` or `num_classes` is excluded automatically. It then
computes per-class IoU, per-class F1, and overall accuracy (OA). Division by
zero can produce NaN for absent classes; the epoch code uses `np.nanmean` for
aggregate values.

For `log_name` containing `vaihingen`, `potsdam`, `whubuilding`,
`massbuilding`, or `cropland`, epoch mIoU and F1 average `[:-1]`, excluding the
last confusion-matrix class. The checked-in Vaihingen/Potsdam class tuple is
`('ImSurf', 'Building', 'LowVeg', 'Tree', 'Car', 'Clutter')`, so its reported
aggregate excludes the last slot. For other names, including the checked-in
`uavid` and `loveda` names, all confusion-matrix classes are averaged; their
ignore pixels are still filtered by the evaluator. The output per-class IoU
is zipped with `config.classes`, while the ignored value is not a class slot.

Compare like with like: preserve the dataset token in `log_name`, save the
raw per-class values, and state whether the last class was excluded. A high
OA can coexist with poor minority-class IoU; inspect all three aggregates and
per-class output.

## 8. Seed, accelerator, and memory strategy

The script always calls `seed_everything(42)`; there is no config seed field
and no CLI override. Python, NumPy, Torch, and CUDA RNGs are seeded, but
cuDNN deterministic and benchmark flags are both enabled. Record the actual
GPU, CUDA/PyTorch versions, batch/crop dimensions, and worker count when
comparing runs.

The trainer uses `devices=config.gpus`, `accelerator='auto'`, and
`strategy='auto'`. Existing configs use `gpus='auto'`; a list such as `[0]` or
a Lightning-supported device count may be used only after checking the
installed PyTorch Lightning version. The verified inspection hardware passed
an A100 CUDA smoke check, but that does not establish compatibility for every
GPU or optional model.

If a valid configuration runs out of memory, do not first alter class counts,
losses, or label values. Reduce `train_batch_size` and, if needed,
`val_batch_size`; then reduce the model's crop/input size or worker/prefetch
pressure while preserving the experiment's declared protocol. Gradient
accumulation is not wired by `accumulate_n` in this script, so adding that
field alone will not recover the effective batch size. Keep a small-batch
smoke run separate from the full result and label it accordingly.
