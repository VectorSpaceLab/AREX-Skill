# Configuration Reference

This reference is a self-contained guide for authoring pytorch-semseg YAML configs and selecting dataset loaders. It is intentionally static: use the validator in `scripts/validate_config.py` before running training or validation.

## Required top-level structure

A practical config has three main sections:

```yaml
model:
  arch: fcn8s

data:
  dataset: pascal
  train_split: train_aug
  val_split: val
  img_rows: 512
  img_cols: 512
  path: datasets/VOC2012
  sbd_path: datasets/benchmark_RELEASE   # Pascal/SBD only

training:
  train_iters: 300000
  batch_size: 1
  n_workers: 4
  val_interval: 1000
  print_interval: 50
  optimizer:
    name: sgd
    lr: 0.0001
    momentum: 0.99
    weight_decay: 0.0005
  loss:
    name: cross_entropy
  lr_schedule: null
  resume: null
```

Required or strongly expected keys:

| Section | Key | Meaning | Notes |
| --- | --- | --- | --- |
| `model` | `arch` | model registry id | See architecture ids below; constructor internals route to `model-zoo-and-apis`. |
| `data` | `dataset` | dataset loader registry id | Must be one of the dataset keys below. |
| `data` | `train_split`, `val_split` | split names passed to loaders | Split spelling is dataset-specific. |
| `data` | `img_rows`, `img_cols` | transform size tuple | Usually positive integers. The string pair `same` is loader-limited; see below. |
| `data` | `path` | dataset root | Replace placeholder or machine-local example paths before use. |
| `data` | `sbd_path` | Pascal VOC/SBD root | Needed for Pascal augmented split setup; not used by non-Pascal loaders. |
| `training` | `batch_size`, `n_workers` | dataloader settings | `n_workers: 0` is safest for debugging. |
| `training` | `train_iters`, `val_interval`, `print_interval` | loop interval settings | Used by training, not by static validation. |
| `training` | `optimizer` | optimizer section | Use `name` plus optimizer keyword args such as `lr`, `momentum`, `weight_decay`. |
| `training` | `loss` | loss section or `null` | If `null`, training code defaults to cross entropy; if the key is missing, it fails. |
| `training` | `lr_schedule` | scheduler section or `null` | If `null`, scheduler code uses constant LR; if the key is missing, it fails. |
| `training` | `resume` | checkpoint path or `null` | Include the key even when starting from scratch. |
| `training` | `augmentations` | optional augmentation mapping | Omit or set to `null` for no augmentations. |

The training code also accepts a top-level `seed` key; if omitted it uses a default seed.

## Model architecture ids

Valid `model.arch` ids in the registry are:

- `fcn32s`, `fcn16s`, `fcn8s`
- `unet`, `segnet`, `pspnet`, `icnet`, `icnetBN`, `linknet`
- `frrnA`, `frrnB`

This sub-skill validates the id only. For constructor parameters and model-specific pitfalls, use `model-zoo-and-apis`.

## Dataset registry keys and loader signatures

| `data.dataset` | Loader class | Constructor signature | Typical splits |
| --- | --- | --- | --- |
| `pascal` | `pascalVOCLoader` | `(root, sbd_path=None, split='train_aug', is_transform=False, img_size=512, augmentations=None, img_norm=True, test_mode=False)` | `train`, `val`, `trainval`, `train_aug`, `train_aug_val` |
| `camvid` | `camvidLoader` | `(root, split='train', is_transform=False, img_size=None, augmentations=None, img_norm=True, test_mode=False)` | `train`, `val`, `test` |
| `ade20k` | `ADE20KLoader` | `(root, split='training', is_transform=False, img_size=512, augmentations=None, img_norm=True, test_mode=False)` | `training`, `validation` |
| `mit_sceneparsing_benchmark` | `MITSceneParsingBenchmarkLoader` | `(root, split='training', is_transform=False, img_size=512, augmentations=None, img_norm=True, test_mode=False)` | `training`, `validation` |
| `cityscapes` | `cityscapesLoader` | `(root, split='train', is_transform=False, img_size=(512, 1024), augmentations=None, img_norm=True, version='cityscapes', test_mode=False)` | `train`, `val`, `test` |
| `nyuv2` | `NYUv2Loader` | `(root, split='training', is_transform=False, img_size=(480, 640), augmentations=None, img_norm=True, test_mode=False)` | config `training` maps to data folder `train`; config `val` maps to data folder `test` |
| `sunrgbd` | `SUNRGBDLoader` | `(root, split='training', is_transform=False, img_size=(480, 640), augmentations=None, img_norm=True, test_mode=False)` | config `training` maps to data folder `train`; config `val` maps to data folder `test` |
| `vistas` | `mapillaryVistasLoader` | `(root, split='training', img_size=(640, 1280), is_transform=True, augmentations=None, test_mode=False)` | `training`, `validation`, sometimes `testing` for image-only use |

Loader notes:

- Training/validation entry points pass only `root`, `split`, `is_transform`, `img_size`, and augmentations. Extra data keys are not automatically forwarded unless an entry point is adapted.
- Pascal's loader has an `sbd_path` constructor argument, but the unmodified training/validation scripts do not forward `data.sbd_path`. If you need Pascal augmented setup, plan an adapter or use a workflow that explicitly passes `sbd_path`.
- CamVid ignores the config `img_size` argument and uses its internal `[360, 480]` transform size.
- Some loaders build paths by string concatenation instead of robust joins. If a loader unexpectedly searches for a malformed path, normalize `data.path` so the final constructed layout matches the examples in [data-formats.md](data-formats.md).

## Registry keys

### Losses

Valid `training.loss.name` values:

- `cross_entropy`
- `bootstrapped_cross_entropy`
- `multi_scale_cross_entropy`

`training.loss: null` selects the default cross entropy path. A missing `training.loss` key is not equivalent to `null` and will fail later.

### Optimizers

Valid `training.optimizer.name` values:

- `sgd`, `adam`, `asgd`, `adamax`, `adadelta`, `adagrad`, `rmsprop`

Place optimizer parameters under `training.optimizer`, for example:

```yaml
training:
  optimizer:
    name: sgd
    lr: 0.0001
    momentum: 0.99
    weight_decay: 0.0005
```

Do not leave `momentum` or `weight_decay` as direct children of `training`; the unmodified code does not forward them into the optimizer from there.

### LR schedulers

Valid `training.lr_schedule.name` values:

- `constant_lr`
- `poly_lr`
- `multi_step`
- `cosine_annealing`
- `exp_lr`

Set `training.lr_schedule: null` for no explicit schedule. If using warmup, the scheduler code looks for `warmup_iters`, `warmup_mode`, and `warmup_factor` inside `lr_schedule`.

### Augmentations

Valid `training.augmentations` keys:

| Key | Parameter form | Effect |
| --- | --- | --- |
| `gamma` | number | random gamma in `[1, 1 + value]` |
| `hue` | number | random hue in `[-value, value]` |
| `brightness` | number | random brightness factor in `[1 - value, 1 + value]` |
| `saturation` | number | random saturation factor in `[1 - value, 1 + value]` |
| `contrast` | number | random contrast factor in `[1 - value, 1 + value]` |
| `rcrop` | number or `[h, w]` | random crop |
| `hflip` | probability | random horizontal flip |
| `vflip` | probability | random vertical flip |
| `scale` | number | resize shorter/longer side while preserving aspect ratio according to loader helper |
| `rsize` | number | random resize then crop |
| `rsizecrop` | number | random sized crop fallback to scale + center crop |
| `rotate` | degrees | random rotation in `[-degrees, degrees]` |
| `translate` | `[dx, dy]` | random reflective translation |
| `ccrop` | number or `[h, w]` | center crop |

Example:

```yaml
training:
  augmentations:
    hflip: 0.5
    rotate: 10
    rcrop: [512, 512]
```

Unsupported augmentation keys raise registry errors later; catch them with `scripts/validate_config.py`.

## `img_rows` / `img_cols`

Recommended default: use positive integers.

The special value must be written as a pair:

```yaml
data:
  img_rows: same
  img_cols: same
```

Known behavior:

- Supported by loaders whose transform explicitly checks for `("same", "same")`: Pascal, MIT Scene Parsing Benchmark, and Mapillary Vistas.
- Not safe for loaders without that check: Cityscapes, ADE20K, NYUv2, and SUNRGBD expect numeric resize dimensions during transform.
- CamVid ignores the config-provided `img_size` and always uses its internal transform size.
- Mixing `same` with a number is invalid.

## Safe templates

### Generic integer-size template

```yaml
model:
  arch: unet

data:
  dataset: cityscapes
  train_split: train
  val_split: val
  img_rows: 512
  img_cols: 1024
  path: datasets/cityscapes

training:
  train_iters: 1000
  batch_size: 2
  n_workers: 0
  val_interval: 100
  print_interval: 10
  optimizer:
    name: adam
    lr: 0.0001
  loss:
    name: cross_entropy
  lr_schedule: null
  resume: null
```

### Pascal with SBD-aware warning

```yaml
model:
  arch: fcn8s

data:
  dataset: pascal
  train_split: train_aug
  val_split: val
  img_rows: same
  img_cols: same
  path: datasets/VOC2012
  sbd_path: datasets/benchmark_RELEASE

training:
  train_iters: 1000
  batch_size: 1
  n_workers: 0
  val_interval: 100
  print_interval: 10
  optimizer:
    name: sgd
    lr: 0.0001
    momentum: 0.99
    weight_decay: 0.0005
  loss:
    name: cross_entropy
  lr_schedule: null
  resume: null
```

Before running this with the unmodified entry points, remember that `data.sbd_path` is not automatically passed into the Pascal loader.

## Legacy config drift warnings

Older or example configs may contain keys that look familiar but are not consumed by the current training path:

| Legacy/drift key | Problem | Safer replacement |
| --- | --- | --- |
| `training.l_rate` | Not read by optimizer setup | `training.optimizer.lr` |
| `training.l_schedule` | Not read by scheduler setup | `training.lr_schedule` |
| `training.momentum` | Not forwarded into optimizer | `training.optimizer.momentum` |
| `training.weight_decay` | Not forwarded into optimizer | `training.optimizer.weight_decay` |
| missing `training.loss` | Later code indexes this key | add `loss: {name: cross_entropy}` or `loss: null` |
| missing `training.lr_schedule` | Later code indexes this key | add `lr_schedule: null` or a scheduler mapping |
| missing `training.resume` | Later code indexes this key | add `resume: null` for fresh training |
| `yaml.load(fp)` in adapted scripts | Modern PyYAML requires an explicit loader | use `yaml.safe_load(fp)` |

Use the static checker to detect these before training:

```bash
python scripts/validate_config.py --config CONFIG.yml --print-summary
```
