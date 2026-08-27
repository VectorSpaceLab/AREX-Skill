# Config reference

MMOCR uses Python config files for model assembly, dataloaders, schedules, hooks, runtime settings, and evaluation. Use this reference when the task is to read, adjust, or validate a config before training or testing. The bundled smoke helper mirrors the safe part of MMOCR's launcher behavior: it loads a config with `Config.fromfile`, applies optional `--cfg-options`, and prints a compact summary without building a runner.

## What the smoke helper prints

| Field | Why it matters |
| --- | --- |
| `default_scope` | Registry root. MMOCR configs usually set this to `mmocr`. |
| `model.type` | Model family selector. This should match the checkpoint family. |
| `work_dir` | Where logs and checkpoints go when a launcher receives or resolves a work directory. |
| `resume` | Training recovery flag. Do not confuse it with evaluation checkpoint selection. |
| `load_from` | Explicit checkpoint or pretrained weight source in config. |
| `optim_wrapper.type` | Precision and optimizer wrapper gate. |
| `auto_scale_lr.base_batch_size` | Required before enabling automatic learning-rate scaling. |
| `train_cfg` / `val_cfg` / `test_cfg` | Run length and loop type. |
| `train_dataloader` / `val_dataloader` / `test_dataloader` | Batch sizing, dataset type, annotation path, and pipeline shape. |
| `val_evaluator` / `test_evaluator` | Metric family and prefixing. |
| `tta_pipeline` / `tta_model` | Recognition TTA route used only by configs that define both fields. |
| `env_cfg.dist_cfg.backend` | Distributed backend, commonly `nccl` for GPU runs. |

## Inheritance and `_base_`

MMOCR prefers Python config inheritance.

- `_base_` can be a string or list of base config files.
- A config can reference values from bases through `_base_.name`.
- Dict-like values can be edited with `.update(...)` or attribute assignment.
- List values can be replaced or edited after copying them from `_base_`.
- Variables with the same name cannot exist in each `_base_` profile.

Typical pattern:

```python
_base_ = [
    '_base_dbnet_resnet18_fpnc.py',
    '../_base_/datasets/icdar2015.py',
    '../_base_/default_runtime.py',
    '../_base_/schedules/schedule_sgd_1200e.py',
]

icdar2015_textdet_train = _base_.icdar2015_textdet_train
icdar2015_textdet_train.pipeline = _base_.train_pipeline
icdar2015_textdet_test = _base_.icdar2015_textdet_test
icdar2015_textdet_test.pipeline = _base_.test_pipeline
```

Dict and list edits are normal Python edits:

```python
icdar2015_textdet_train = _base_.icdar2015_textdet_train
icdar2015_textdet_train.update(pipeline=_base_.train_pipeline)
```

```python
_base_ = ['pseudo.py']
pseudo = _base_.pseudo
pseudo[2] = 4
```

## Command-line overrides

Use `--cfg-options` when the change is temporary and should not become a new config file.

```bash
mim train mmocr CONFIG --cfg-options optim_wrapper.optimizer.lr=1e-4
```

Rules that matter in practice:

- Use dotted paths for nested keys.
- Keep each override as one `key=value` token.
- Quote list or tuple overrides exactly so the shell does not split them.
- Run the same override through the smoke helper before training:

```bash
python scripts/mmocr_config_smoke.py --config CONFIG \
  --cfg-options 'optim_wrapper.optimizer.lr=1e-4'
```

## Fields to check before a run

### Model and runtime

- `default_scope` should normally be `mmocr`.
- `model.type` should match the family you intend to run.
- `load_from` should point to a compatible checkpoint or stay empty when starting from scratch.
- `resume=True` should only be used when recovering training state from the latest checkpoint in the resolved work directory.

### Schedule and precision

- `optim_wrapper.type` controls whether AMP can be enabled safely.
- `auto_scale_lr.base_batch_size` must exist before enabling automatic LR scaling.
- `train_cfg.max_epochs` and `train_cfg.val_interval` describe run length and validation frequency.
- `param_scheduler` should match the max epoch or iteration budget in the config family.

### Data and evaluation

- `train_dataloader`, `val_dataloader`, and `test_dataloader` should agree with storage backend and dataset family.
- `train_dataloader.dataset.pipeline` should match the dataset loader, especially for LMDB-backed recognition data.
- `val_evaluator` and `test_evaluator` should match the task: detection metrics for text detection, recognition metrics for text recognition, and F1-style metrics for KIE.
- `tta_pipeline` and `tta_model` are only relevant when the config supports recognition TTA.

## Practical selection rule

- If the smoke helper fails, fix the config first.
- If the smoke helper passes but the wrong family or evaluator is selected, edit `_base_` or use `--cfg-options`.
- If only one launch needs a change, prefer `--cfg-options`.
- If the same tweak will be reused, write a new config that inherits from the family base.
