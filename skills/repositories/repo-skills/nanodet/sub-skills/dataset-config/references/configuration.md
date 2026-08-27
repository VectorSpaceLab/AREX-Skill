# Configuration

NanoDet uses YAML configs loaded into a mutable `CfgNode` and then frozen.
The config drives model assembly, dataset construction, preprocessing, optimizer settings, and logging.

## Top-level sections

| Section | Purpose |
| --- | --- |
| `save_dir` | Output directory for logs, checkpoints, and evaluation artifacts |
| `model` | Model family, backbone, neck/FPN, head, and optional weight averaging |
| `data` | Train/val dataset definitions and preprocessing pipelines |
| `device` | GPU IDs, worker count, batch size, and precision |
| `schedule` | Optimizer, warmup, total epochs, LR schedule, resume/load checkpoint |
| `evaluator` | Validation metric backend and `save_key` |
| `log` | Log interval |
| `class_names` | Ordered list of class names used by the head and visualization |

## Model section

The verified build path supports these assemblies:

- `OneStageDetector`
- `NanoDetPlus`
- deprecated alias `GFL` → `OneStageDetector`

A model usually contains:

- `backbone`
- `fpn`
- `head`
- optional `weight_averager`
- for NanoDet-Plus, an optional `aux_head`

### Common backbone fields

| Field | Meaning |
| --- | --- |
| `name` | Backbone class name |
| `model_size` / `arch` | Variant selector for ShuffleNetV2 / RepVGG / other backbones |
| `out_stages` | Which feature levels to return |
| `activation` | Activation layer name |
| `deploy` | RepVGG deploy toggle |
| `pretrained` | Whether to load pretrained weights when the backbone supports it |

### Common head fields

| Field | Meaning |
| --- | --- |
| `name` | Head class name |
| `num_classes` | Number of object classes, excluding background |
| `input_channel` | Input channel count from the neck |
| `feat_channels` | Hidden channel width |
| `stacked_convs` | Number of conv layers in each branch |
| `strides` | Feature strides used by the head |
| `reg_max` | Discrete regression-bin size |
| `loss` | Loss family and loss weights |

## Data section

The `data.train` and `data.val` blocks usually contain:

- `name`: dataset class name.
- `img_path`: image root.
- `ann_path`: annotation file or directory.
- `input_size`: `[width, height]`.
- `keep_ratio`: preserve aspect ratio during resize.
- `multi_scale`: optional training-time size jitter.
- `pipeline`: augmentation and normalization settings.

### Pipeline fields commonly used in the repo

- `perspective`
- `scale`
- `stretch`
- `rotation`
- `shear`
- `translate`
- `flip`
- `brightness`
- `contrast`
- `saturation`
- `normalize`

## Device section

- `gpu_ids: -1` selects CPU mode in the train/test scripts.
- A list such as `[0]` or `[0, 1]` selects GPU training when available.
- `precision: 16` enables AMP training where supported.

## Schedule section

- `resume` reuses the last training checkpoint in `save_dir`.
- `load_model` loads a specific checkpoint before training.
- `optimizer` names a `torch.optim` class.
- `warmup` supports `constant`, `linear`, and `exp`.
- `lr_schedule` maps to a PyTorch LR scheduler class.
- `val_intervals` controls validation frequency.

## Validation rules worth remembering

- `cfg.model.arch.head.num_classes` must equal `len(cfg.class_names)`.
- The config must name a supported dataset, backbone, neck, head, and evaluator.
- `TIMMWrapper` configs require `timm`.
- Some configs default to pretrained backbone downloads unless you override that setting.
