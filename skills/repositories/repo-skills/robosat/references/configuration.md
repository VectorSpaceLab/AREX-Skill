# Configuration

RoboSat uses simple TOML files for both dataset and model settings.

## Dataset TOML

The sample dataset config in the repository shows the main fields:

```toml
[common]
dataset = '/path/to/dataset-root/'
classes = ['background', 'parking']
colors  = ['denim', 'orange']

[weights]
values = [1.6248, 5.762827]
```

### Field meanings

| Field | Meaning |
| --- | --- |
| `common.dataset` | Root directory containing `training/` and `validation/` Slippy Map subtrees. |
| `common.classes` | Ordered class names. The index of a class is the mask pixel value used by training and post-processing. |
| `common.colors` | Ordered Mapbox color names for palettes and mask visualization. The number of colors should match the number of classes. |
| `weights.values` | Class weights list for weighted losses and `rs train`. Generate it with `rs weights --dataset dataset.toml`. |

### Layout expectations

The dataset root should contain:

- `training/images/`
- `training/labels/`
- `validation/images/`
- `validation/labels/`

Each subtree must be a Slippy Map `z/x/y.ext` tree, and the image and label tile sets should match.

## Model TOML

The sample model config in the repository shows the main fields:

```toml
[common]
cuda = false
batch_size = 2
image_size = 512
checkpoint = '/path/to/checkpoints/'

[opt]
epochs = 10
lr = 0.0001
loss = 'Lovasz'
```

### Field meanings

| Field | Meaning |
| --- | --- |
| `common.cuda` | Toggle CUDA execution in `train`, `predict`, and `serve`. Leave `false` for the CPU-safe path. |
| `common.batch_size` | Batch size used for training and prediction data loaders. |
| `common.image_size` | Square side length in pixels used to resize/crop tiles. Must be divisible by 32 for the ResNet encoder. |
| `common.checkpoint` | Directory where training writes `.pth` checkpoints, logs, and history figures. |
| `opt.epochs` | Number of epochs to train. |
| `opt.lr` | Adam learning rate. |
| `opt.loss` | Loss name: `Lovasz`, `CrossEntropy`, `mIoU`, or `Focal`. |

### Loss and weights interaction

- `Lovasz` does not require `weights.values`.
- `CrossEntropy`, `mIoU`, and `Focal` expect `weights.values` in the dataset TOML.
- The training loop loads the weights as a tensor and uses them in the selected loss.

## Template generation

Use `scripts/create_config_templates.py` to write a CPU-safe starting pair of TOML files:

```bash
python scripts/create_config_templates.py --out-dir <config-dir>
```

The script writes `dataset.toml` and `model.toml` with conservative defaults and a CPU-safe `cuda = false` setting.

## Validation checklist

Before launching `rs train` or `rs predict`:

1. The dataset root exists and contains both training and validation splits.
2. Images and labels cover the same tile ids.
3. The tile size in the model config matches the tile size of the prepared Slippy Map data.
4. `image_size` is divisible by 32.
5. If using a weighted loss, the dataset TOML contains a weight list.
6. If using CUDA, a compatible torch CUDA environment has already passed a smoke check.
