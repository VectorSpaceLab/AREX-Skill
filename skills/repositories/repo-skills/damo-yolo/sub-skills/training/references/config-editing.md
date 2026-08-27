# DAMO-YOLO config editing guide

DAMO-YOLO config files are Python modules. `parse_config(config_file)` imports the module and instantiates a class named `Config` that inherits from `damo.config.Config`.

## Start from a copied config

Create a user-owned config file from the model variant that is closest to your target size and latency. If the source config reads TinyNAS structure text with a relative path such as `./damo/base_models/backbones/...`, either keep the same asset layout under the work directory you pass to bundled scripts, or rewrite the config to read the structure from an absolute/user-owned path.

Use `--workdir` with bundled scripts to define the directory that config-relative paths should resolve from:

```bash
sub-skills/training/scripts/launch_train.sh \
  --config /path/to/my_damoyolo_custom.py \
  --workdir /path/used/by/config-relative-assets \
  --gpus 1 --dry-run
```

## High-value keys

| Area | Key or pattern | Notes |
|---|---|---|
| Experiment name | `self.miscs.exp_name` | Defaults to the config filename stem in model configs. Used for logs/checkpoints under `output_dir`. |
| Output | `self.miscs.output_dir` | Defaults to `./workdirs` in base config. Training writes under `output_dir/exp_name`. |
| Intervals | `self.miscs.eval_interval_epochs`, `self.miscs.ckpt_interval_epochs`, `self.miscs.print_interval_iters` | Controls eval, checkpoint, and log cadence during training. |
| Workers | `self.miscs.num_workers` | DataLoader workers. Reduce for small machines or debugging. |
| Train batch | `self.train.batch_size` | Must be divisible by training GPU count. Used by LR scheduler and dataloader. |
| Eval batch | `self.test.batch_size` | Must be divisible by eval GPU count. |
| Epochs | `self.train.total_epochs`, `self.train.warmup_epochs`, `self.train.no_aug_epochs` | `no_aug_epochs` disables mosaic/mixup near the end. |
| LR schedule | `self.train.base_lr_per_img`, `self.train.min_lr_ratio`, `self.train.warmup_start_lr` | `Trainer` computes LR as `base_lr_per_img * batch_size` with cosine decay. |
| Optimizer | `self.train.optimizer` | Base config contains the optimizer dict used by `Trainer.build_optimizer()`. Edit this dict if changing optimizer hyperparameters. |
| Dataset names | `self.dataset.train_ann`, `self.dataset.val_ann` | Tuples of names returned by `get_data()`; training currently supports only one training dataset name, while validation may list multiple datasets. |
| Class names | `self.dataset.class_names` | Required by `COCODataset`; order defines contiguous labels. |
| Detection head | `self.model.head['num_classes']`, `nms_conf_thre`, `nms_iou_thre` | `num_classes` must match class names and checkpoint head. NMS thresholds are reliable config edits for eval. |
| Fine-tune | `self.train.finetune_path` | Loads detector weights and starts from epoch 0. |
| Resume | `self.train.resume_path` | Restores model/optimizer/epoch from a training checkpoint. |

## Command-line `opts` caveat

The bundled train/eval entry points preserve the source parser's trailing `opts`, but `Config.merge()` only updates attributes whose exact key exists on the config object. Nested keys such as `train.batch_size` or `model.head.num_classes` are not handled like YACS-style dotted options.

Use edited config files for durable changes. If a future fork changes `merge()` semantics, verify with a small `parse_config()` probe before relying on CLI overrides.

## Checkpoint expectations

Fine-tune:

```python
self.train.finetune_path = 'checkpoints/pretrained_detector.pth'
self.train.resume_path = None
```

- Uses `model.load_pretrain_detector(path)`.
- Suitable for changing dataset or class count when the loader can ignore/adapt unmatched head weights.
- Starts epoch counters from 0.

Resume:

```python
self.train.finetune_path = None
self.train.resume_path = 'workdirs/my_exp/latest_ckpt.pth'
```

- Uses `torch.load()` and strict `model.load_state_dict(ckpt['model'])`.
- Restores `ckpt['optimizer']` and `ckpt['epoch']`.
- Distillation resume also expects `ckpt['feature_loss']` when distillation is active.
- Do not use for architecture/class-count changes.

Eval with the bundled launcher:

```bash
sub-skills/training/scripts/launch_eval.sh \
  --config /path/to/my_damoyolo_custom.py \
  --workdir /path/used/by/config-relative-assets \
  --ckpt /path/to/eval_model.pth \
  --gpus 1 --fuse
```

- Expects a checkpoint dict with a `model` key, or a compatible raw state dict.
- Loads with `strict=False` after stripping the substring `module` from keys.
- `--fuse` is applied. Parsed flags `--conf`, `--nms`, `--tsize`, `--seed`, and `--test` are preserved for source compatibility, but prefer config edits for reliable behavior.

## Dataset path behavior

The base `get_data()` uses `DatasetCatalog.DATA_DIR` and `DatasetCatalog.DATASETS` from `damo.config.paths_catalog` when the dataset name contains `coco`. The base `dataset.data_dir` and `dataset.paths_catalog` fields are not consulted by the default `get_data()` implementation.

Therefore, to redirect data reliably:

1. Edit `DatasetCatalog.DATA_DIR` or add entries under `DatasetCatalog.DATASETS` in a config-accessible module; or
2. Override `get_data()` in the custom config class and return `{'factory': 'COCODataset', 'args': {'root': ..., 'ann_file': ...}}`; or
3. Use the bundled validator's `--data-root` for validation only, then make the same path resolution explicit in the config before training/eval.

Keep `dataset.train_ann` to a single dataset name for training. `build_dataloader()` asserts that multi-training-set loading is not supported yet.

## Small-run debugging edits

For smoke/debug runs only, reduce cost in a copied config:

```python
self.train.batch_size = 8      # keep divisible by GPU count
self.test.batch_size = 8
self.train.total_epochs = 1
self.miscs.eval_interval_epochs = 1
self.miscs.ckpt_interval_epochs = 1
self.miscs.num_workers = 0
```

Do not publish smoke settings as production defaults unless the user explicitly wants a tiny run.
