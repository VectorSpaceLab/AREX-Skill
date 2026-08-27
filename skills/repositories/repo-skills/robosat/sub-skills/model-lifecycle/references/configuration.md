# Configuration

RoboSat model lifecycle commands read TOML files. The model config controls execution behavior and the dataset config describes class order, colors, and the training root.

## Model config

Typical fields in `model-unet.toml`:

```toml
[common]
cuda = false
batch_size = 2
image_size = 512
checkpoint = "CHECKPOINT_DIR"

[opt]
epochs = 10
lr = 0.0001
loss = "Lovasz"
```

### `common`

| Field | Meaning | Notes |
| --- | --- | --- |
| `cuda` | Use CUDA when `true`, CPU when `false`. | `train`, `predict`, and `serve` exit if CUDA is requested but unavailable. |
| `batch_size` | Mini-batch size for train and validation loaders. | Choose a size that fits memory and does not collapse tiny splits when `drop_last=True`. |
| `image_size` | Square side length in pixels for training inputs. | Must be divisible by 32 so the U-Net / ResNet encoder-decoder shape stays valid. |
| `checkpoint` | Writable directory for model artifacts. | Training writes `.pth`, `log`, and `history-*.png` files here. |

### `opt`

| Field | Meaning | Notes |
| --- | --- | --- |
| `epochs` | Total number of epochs to train. | Resuming from a checkpoint fails if the checkpoint epoch already reached this limit. |
| `lr` | Adam learning rate. | The current CLI uses Adam with this scalar. |
| `loss` | Loss family name. | Supported values are `CrossEntropy`, `mIoU`, `Focal`, and `Lovasz`. |

## Dataset config

Typical fields in `dataset-parking.toml`:

```toml
[common]
dataset = "DATASET_ROOT"
classes = ["background", "parking"]
colors = ["denim", "orange"]

[weights]
values = [1.6248, 5.762827]
```

### `common`

| Field | Meaning | Notes |
| --- | --- | --- |
| `dataset` | Root slippy-map dataset directory. | Training expects `training/images`, `training/labels`, `validation/images`, and `validation/labels` under this root. |
| `classes` | Ordered class labels. | `len(classes)` determines `num_classes` for the model. Keep background first and foreground second for the binary workflows. |
| `colors` | Ordered palette names for masks. | Must use names understood by `robosat.colors.Mapbox`. The order should match `classes`. |

### `weights`

| Field | Meaning | Notes |
| --- | --- | --- |
| `values` | Per-class weights. | Required when `loss` is `CrossEntropy`, `mIoU`, or `Focal`. Must have one value per class. |

## Relationship rules

- `len(dataset.common.classes)` determines the model output channel count everywhere.
- `len(dataset.weights.values)` must match the class count when the selected loss uses class weights.
- `dataset.common.colors` must also match the class count if you want palette-based mask rendering.
- `image_size` for training and `tile_size` for prediction / serving should both stay square and divisible by 32.
- The checkpoint directory is a directory, not a file path.
- The saved checkpoint payload is a dictionary with `epoch`, `state_dict`, and `optimizer`.
- The checkpoint `state_dict` comes from a `DataParallel` wrapped model, so a custom loader may need the same wrapper or a prefix cleanup step.

## Device selection

- `cuda = false` is the safest default for smoke tests and CPU-only environments.
- `cuda = true` is only valid when a matching CUDA PyTorch build is available and `torch.cuda.is_available()` is true.
- Export still loads the checkpoint on CPU, but it uses the same class count and image size assumptions as the model stack.

## What is not configured here

- Dataset extraction and rasterization live in the data-preparation route.
- Probability-to-mask and GeoJSON post-processing live in the feature-postprocessing route.
