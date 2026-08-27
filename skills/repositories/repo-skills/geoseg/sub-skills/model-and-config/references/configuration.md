# Configuration guide

## How configs work

A config is an executable Python module, not a declarative YAML file. The
training entry point calls `py2cfg(config_path)`, which imports the config's
parent directory and returns every non-dunder module global in an
`addict.Dict`-like `ConfigDict`. `ConfigDict.__missing__` and `__getattr__`
raise on absent fields. `object_from_dict` can resolve a `type` name with
`pydoc.locate`, but the checked-in configs construct their objects directly.

Use `scripts/inspect_config.py` for a static report before using `py2cfg`. It
parses the AST and never imports the config by default. This matters because a
config imports a dataset module, constructs datasets and models, creates
optimizers/schedulers, and may load weights at import time. In particular,
`geoseg.datasets.loveda_dataset` creates `loveda_val_dataset` at module import,
which immediately enumerates `data_root/Urban/images_png`,
`data_root/Urban/masks_png_convert`, and the corresponding Rural directories.
The checkout has no data or checkpoint assets, so do not claim that a checked-in
config imports successfully in a clean checkout.

## Shared field contract

The configs expose these groups of fields:

- **Task/labels:** `classes`, `num_classes`, `ignore_index`.
- **Run length/batching:** `max_epoch`, `train_batch_size`, `val_batch_size`,
  sometimes `accumulate_n`.
- **Checkpoint/logging:** `weights_name`, `weights_path`, `test_weights_name`,
  `log_name`, `monitor`, `monitor_mode`, `save_top_k`, `save_last`,
  `check_val_every_n_epoch`, `pretrained_ckpt_path`, `resume_ckpt_path`.
- **Runtime:** `gpus` (usually `'auto'`).
- **Objects:** `net`, `loss`, `train_dataset`, `val_dataset`, optionally
  `test_dataset`, `train_loader`, `val_loader`, `optimizer`, and
  `lr_scheduler`.
- **Supervision:** `use_aux_loss`. It must agree with the model's training
  return shape and the selected loss implementation.

`monitor` is consumed by Lightning `ModelCheckpoint` and must be one of the
metrics logged by `Supervision_Train`: `val_mIoU`, `val_F1`, or `val_OA`.
`monitor_mode='max'` selects the largest value. `weights_path` is the directory
for Lightning checkpoints; `test_weights_name` is the filename stem used by the
repository test scripts. `save_last` controls whether a `last.ckpt` is also
written, and `save_top_k` controls how many monitored checkpoints are retained.

## Checked-in config matrix

Values below are source-verified. Dataset roots are relative to the process
working directory and are expected to be prepared using the repository's data
preprocessing workflow. Optimizers use `tools.utils.process_model_params` with
`layerwise_params={"backbone.*": {lr: backbone_lr,
weight_decay: backbone_weight_decay}}`, then wrap AdamW in `Lookahead`.

| Config | Model / class count | Ignore | Loss / aux | Main run fields | Scheduler |
| --- | --- | ---: | --- | --- | --- |
| `loveda/unetformer.py` | `UNetFormer`, 7 | 7 | `UnetFormerLoss`, yes | 30 epochs, train/val 16, lr `6e-4`, wd `0.01`, backbone lr `6e-5` | `CosineAnnealingLR(T_max=30, eta_min=1e-6)` |
| `loveda/dcswin.py` | `dcswin_small`, 7 | 7 | `JointLoss(SoftCrossEntropyLoss(.05), DiceLoss(.05))`, no | 30 epochs, 8/8, lr `6e-4`, wd `0.01`, backbone lr `6e-5`; explicit small weight path | `CosineAnnealingLR(T_max=30, eta_min=1e-6)` |
| `potsdam/unetformer.py` | `UNetFormer`, 6 | 6 | `UnetFormerLoss`, yes | 45 epochs, 8/8, lr `6e-4`, wd `0.01`, backbone lr `6e-5` | `CosineAnnealingWarmRestarts(T_0=15,T_mult=2)` |
| `potsdam/dcswin.py` | `dcswin_small`, 6 | 6 | `JointLoss` of smoothed CE + Dice, no | 30 epochs, 8/4, lr `1e-3`, wd `2.5e-4`, backbone lr `1e-4` | `CosineAnnealingWarmRestarts(T_0=10,T_mult=2)` |
| `potsdam/ftunetformer.py` | `ft_unetformer(decoder_channels=256)`, 6 | 6 | `JointLoss` of smoothed CE + Dice, no | 45 epochs, 4/4, lr `6e-4`, wd `2.5e-4`, backbone lr `6e-5` | `CosineAnnealingWarmRestarts(T_0=15,T_mult=2)` |
| `uavid/unetformer.py` | `UNetFormer`, 8 | 255 | `UnetFormerLoss`, yes | 40 epochs, 8/8, lr `6e-4`, wd `0.01`, backbone lr `6e-5` | `CosineAnnealingLR(T_max=40)` |
| `vaihingen/unetformer.py` | `UNetFormer`, 6 | 6 | `UnetFormerLoss`, yes | 105 epochs, 8/8, lr `6e-4`, wd `0.01`, backbone lr `6e-5` | `CosineAnnealingWarmRestarts(T_0=15,T_mult=2)` |
| `vaihingen/dcswin.py` | `dcswin_small`, 6 | 6 | `JointLoss` of smoothed CE + Dice, no | 70 epochs, 8/4, lr `1e-3`, wd `2.5e-4`, backbone lr `1e-4`; `accumulate_n=1` | `CosineAnnealingWarmRestarts(T_0=10,T_mult=2)` |
| `vaihingen/ftunetformer.py` | `ft_unetformer(decoder_channels=256)`, 6 | 6 | `JointLoss` of smoothed CE + Dice, no | 45 epochs, 8/4, lr `6e-4`, wd `2.5e-4`, backbone lr `6e-5` | `CosineAnnealingWarmRestarts(T_0=15,T_mult=2)` |

All configs set `monitor_mode='max'`, `check_val_every_n_epoch=1`, and leave
`pretrained_ckpt_path` and `resume_ckpt_path` as `None`. The save/log naming
strings differ by dataset and are intentionally not interchangeable.

## Loss and auxiliary-head rules

`JointLoss(first, second, first_weight, second_weight)` returns the weighted
sum. The configured first term is smoothed cross entropy (`smooth_factor=.05`)
and the second is `DiceLoss(smooth=.05)`, both using the config ignore value.
`UnetFormerLoss` uses that same main combination and adds `0.4 *
SoftCrossEntropyLoss` on the auxiliary logits when its input is a two-item
`(main, aux)` tuple. If its input is a tensor, it returns only the main loss.

UNetFormer's training output is a tuple, while validation/evaluation output is
a tensor because its `forward` branches on `self.training`. `train_supervision.py`
therefore indexes `prediction[0]` only when `use_aux_loss` is true for training
metrics. A mismatch such as `use_aux_loss=True` with DCSwin, or `False` with a
UNetFormer training tuple passed to `UnetFormerLoss`, is a contract error even
if construction succeeds. FTUNetFormer, DCSwin, MANet, BANet, and A2FPN return
single logits tensors in their normal paths. ABCNet has a source-level
three-output training tuple and needs a separate loss/loop decision.

## Optimizer and parameter groups

`process_model_params` creates one optimizer group per named parameter and
matches ordered regex rules. The checked configs apply lower learning rate and
weight decay to names matching `backbone.*`; bias parameters have weight decay
set to zero by default. The base optimizer is `torch.optim.AdamW`, then
`Lookahead(base_optimizer)` is used. The scheduler is held as a config object
and returned directly by Lightning. Do not copy a scheduler from one config to
another without also checking `max_epoch` and its restart/annealing semantics.

Before training, inspect the optimizer's parameter groups and assert that the
backbone rule matched at least one parameter. If it matched none after a model
rename, the run will silently use the global learning rate for everything.
